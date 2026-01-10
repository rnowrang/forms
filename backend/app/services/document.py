"""Document generation service for DOCX and PDF output."""

import os
import shutil
import subprocess
import re
from typing import Optional, Dict, Any, Tuple
from datetime import datetime

from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from docx import Document
from docx.table import Table
from docx.text.paragraph import Paragraph

from app.config import get_settings
from app.models.template import Template
from app.models.form import FormInstance, FormVersion, FormData

settings = get_settings()


class DocumentService:
    """Service for generating filled DOCX and PDF documents."""
    
    @staticmethod
    def generate_documents(
        db: Session,
        form_id: int,
        version_id: Optional[int] = None
    ) -> Tuple[str, str]:
        """
        Generate filled DOCX and PDF for a form version.
        
        Returns tuple of (docx_path, pdf_path).
        """
        # Get form and template
        form = db.query(FormInstance).filter(FormInstance.id == form_id).first()
        if not form:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Form not found"
            )
        
        template = db.query(Template).filter(Template.id == form.template_id).first()
        if not template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Template not found"
            )
        
        # Get form data (from version or current)
        if version_id:
            version = db.query(FormVersion).filter(FormVersion.id == version_id).first()
            if not version:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Version not found"
                )
            form_data = version.data_snapshot
        else:
            form_data_record = db.query(FormData).filter(
                FormData.form_instance_id == form_id
            ).first()
            form_data = form_data_record.data if form_data_record else {}
        
        # Generate filled DOCX
        docx_path = DocumentService._fill_docx(
            template_path=template.original_file_path,
            schema=template.schema,
            data=form_data,
            form_id=form_id,
            version_id=version_id
        )
        
        # Convert to PDF
        pdf_path = DocumentService._convert_to_pdf(docx_path)
        
        # Update version with document paths if version_id provided
        if version_id:
            version.generated_docx_path = docx_path
            version.generated_pdf_path = pdf_path
            db.commit()
        
        return docx_path, pdf_path
    
    @staticmethod
    def _fill_docx(
        template_path: str,
        schema: Dict[str, Any],
        data: Dict[str, Any],
        form_id: int,
        version_id: Optional[int]
    ) -> str:
        """Fill a DOCX template with form data."""
        # Create output directory
        output_dir = os.path.join(settings.generated_dir, str(form_id))
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate output filename
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        version_suffix = f"_v{version_id}" if version_id else ""
        output_filename = f"form_{form_id}{version_suffix}_{timestamp}.docx"
        output_path = os.path.join(output_dir, output_filename)
        
        # Copy template to output
        shutil.copy(template_path, output_path)
        
        # Open and fill document
        doc = Document(output_path)
        fields = schema.get("fields", [])
        
        # Build field lookup by ID
        field_map = {f["id"]: f for f in fields}
        
        # Fill each field
        for field_id, value in data.items():
            if field_id.startswith("_"):
                continue  # Skip system fields
            
            field_def = field_map.get(field_id)
            if not field_def:
                continue
            
            anchor = field_def.get("anchor")
            if not anchor:
                continue
            
            DocumentService._write_value_to_anchor(doc, anchor, value, field_def)
        
        # Save the filled document
        doc.save(output_path)
        
        return output_path
    
    @staticmethod
    def _write_value_to_anchor(
        doc: Document,
        anchor: Dict[str, Any],
        value: Any,
        field_def: Dict[str, Any]
    ) -> None:
        """Write a value to the anchored location in the document."""
        anchor_type = anchor.get("type")
        
        if anchor_type == "paragraph":
            DocumentService._fill_paragraph_anchor(doc, anchor, value, field_def)
        elif anchor_type == "table_cell":
            DocumentService._fill_table_cell_anchor(doc, anchor, value, field_def)
        elif anchor_type == "table":
            DocumentService._fill_table_anchor(doc, anchor, value, field_def)
    
    @staticmethod
    def _fill_paragraph_anchor(
        doc: Document,
        anchor: Dict[str, Any],
        value: Any,
        field_def: Dict[str, Any]
    ) -> None:
        """Fill a paragraph-anchored field."""
        paragraph_contains = anchor.get("paragraph_contains", "")
        paragraph_index = anchor.get("paragraph_index")
        
        for i, para in enumerate(doc.paragraphs):
            # Match by index or by content
            if paragraph_index is not None and i == paragraph_index:
                DocumentService._insert_value_in_paragraph(para, value, field_def)
                return
            elif paragraph_contains and paragraph_contains.lower() in para.text.lower():
                DocumentService._insert_value_in_paragraph(para, value, field_def)
                return
    
    @staticmethod
    def _insert_value_in_paragraph(
        para: Paragraph,
        value: Any,
        field_def: Dict[str, Any]
    ) -> None:
        """Insert value into a paragraph, preserving formatting."""
        text = para.text
        field_type = field_def.get("type", "text")
        
        # Format value based on type
        if field_type == "checkbox":
            if isinstance(value, list):
                formatted_value = ", ".join(str(v) for v in value)
            else:
                formatted_value = "☑" if value else "☐"
        elif isinstance(value, list):
            formatted_value = ", ".join(str(v) for v in value)
        else:
            formatted_value = str(value) if value else ""
        
        # Find placeholder pattern (underscores or empty after colon)
        # Pattern: label followed by underscores or blank space
        patterns = [
            (r'(_+)', formatted_value),  # Replace underscores
            (r'(:\s*)$', f': {formatted_value}'),  # Append after colon at end
        ]
        
        for pattern, replacement in patterns:
            if re.search(pattern, text):
                new_text = re.sub(pattern, replacement, text, count=1)
                
                # Clear existing runs and add new text
                # Preserve the formatting of the first run
                if para.runs:
                    first_run = para.runs[0]
                    font_name = first_run.font.name
                    font_size = first_run.font.size
                    font_bold = first_run.font.bold
                    
                    # Clear paragraph
                    for run in para.runs:
                        run.text = ""
                    
                    # Add new text with original formatting
                    para.runs[0].text = new_text
                else:
                    para.text = new_text
                return
    
    @staticmethod
    def _fill_table_cell_anchor(
        doc: Document,
        anchor: Dict[str, Any],
        value: Any,
        field_def: Dict[str, Any]
    ) -> None:
        """Fill a table cell-anchored field."""
        table_index = anchor.get("table_index", 0)
        row_index = anchor.get("row_index", 0)
        column_index = anchor.get("column_index", 1)
        
        if table_index >= len(doc.tables):
            return
        
        table = doc.tables[table_index]
        
        if row_index >= len(table.rows):
            return
        
        row = table.rows[row_index]
        
        if column_index >= len(row.cells):
            return
        
        cell = row.cells[column_index]
        
        # Format value
        if isinstance(value, list):
            formatted_value = ", ".join(str(v) for v in value)
        else:
            formatted_value = str(value) if value else ""
        
        # Set cell text while preserving formatting
        if cell.paragraphs:
            para = cell.paragraphs[0]
            # Preserve formatting from existing text
            if para.runs:
                for run in para.runs[1:]:
                    run.text = ""
                para.runs[0].text = formatted_value
            else:
                para.text = formatted_value
        else:
            cell.text = formatted_value
    
    @staticmethod
    def _fill_table_anchor(
        doc: Document,
        anchor: Dict[str, Any],
        value: Any,
        field_def: Dict[str, Any]
    ) -> None:
        """Fill a repeatable table-anchored field."""
        if not isinstance(value, list):
            return
        
        table_index = anchor.get("table_index", 0)
        
        if table_index >= len(doc.tables):
            return
        
        table = doc.tables[table_index]
        repeatable_config = field_def.get("repeatable_config", {})
        columns = repeatable_config.get("columns", [])
        
        # Fill data rows (skip header row)
        for row_idx, row_data in enumerate(value):
            if row_idx + 1 >= len(table.rows):
                # Need to add new row
                table.add_row()
            
            row = table.rows[row_idx + 1]
            
            for col_idx, col_def in enumerate(columns):
                if col_idx >= len(row.cells):
                    continue
                
                cell = row.cells[col_idx]
                col_id = col_def.get("id", f"col_{col_idx}")
                cell_value = row_data.get(col_id, "") if isinstance(row_data, dict) else ""
                
                if cell.paragraphs:
                    cell.paragraphs[0].text = str(cell_value)
                else:
                    cell.text = str(cell_value)
    
    @staticmethod
    def _convert_to_pdf(docx_path: str) -> str:
        """Convert DOCX to PDF using LibreOffice."""
        output_dir = os.path.dirname(docx_path)
        
        # LibreOffice command for headless PDF conversion
        cmd = [
            settings.libreoffice_path,
            '--headless',
            '--convert-to', 'pdf',
            '--outdir', output_dir,
            docx_path
        ]
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60  # 60 second timeout
            )
            
            if result.returncode != 0:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"PDF conversion failed: {result.stderr}"
                )
            
            # PDF file has same name with .pdf extension
            pdf_path = docx_path.replace('.docx', '.pdf')
            
            if not os.path.exists(pdf_path):
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="PDF file was not created"
                )
            
            return pdf_path
            
        except subprocess.TimeoutExpired:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="PDF conversion timed out"
            )
        except FileNotFoundError:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="LibreOffice not found. Please install LibreOffice."
            )
    
    @staticmethod
    def get_document_paths(
        db: Session,
        form_id: int,
        version_id: int
    ) -> Optional[Tuple[str, str]]:
        """Get existing document paths for a version."""
        version = db.query(FormVersion).filter(
            FormVersion.id == version_id
        ).first()
        
        if not version:
            return None
        
        if version.generated_docx_path and version.generated_pdf_path:
            if os.path.exists(version.generated_docx_path) and os.path.exists(version.generated_pdf_path):
                return (version.generated_docx_path, version.generated_pdf_path)
        
        return None
