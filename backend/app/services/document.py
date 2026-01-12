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
from docx.shared import RGBColor

from app.config import get_settings
from app.models.template import Template
from app.models.form import FormInstance, FormVersion, FormData

settings = get_settings()


class DocumentService:
    """Service for generating filled DOCX and PDF documents."""

    @staticmethod
    def _flatten_dict(d: Dict[str, Any], parent_key: str = '', sep: str = '.') -> Dict[str, Any]:
        """
        Flatten a nested dictionary to dot-notation keys.

        Example: {'personnel': {'pi_name': 'John'}} -> {'personnel.pi_name': 'John'}
        """
        items = []
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(DocumentService._flatten_dict(v, new_key, sep).items())
            else:
                items.append((new_key, v))
        return dict(items)

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

        # Flatten nested data to dot-notation keys (e.g., personnel.pi_name)
        flat_data = DocumentService._flatten_dict(data)

        # Handle Section C contact fields specially (row 9 is fully merged)
        # Combine contact_name, contact_ext, contact_email into one value
        contact_fields = ['personnel.contact_name', 'personnel.contact_ext', 'personnel.contact_email']
        contact_values = {f: flat_data.get(f, '') for f in contact_fields}
        if any(contact_values.values()):
            # Format: "Name | Ext: xxx | Email: xxx"
            parts = []
            if contact_values['personnel.contact_name']:
                parts.append(str(contact_values['personnel.contact_name']))
            if contact_values['personnel.contact_ext']:
                parts.append(f"Ext: {contact_values['personnel.contact_ext']}")
            if contact_values['personnel.contact_email']:
                parts.append(f"Email: {contact_values['personnel.contact_email']}")
            combined_contact = " | ".join(parts)

            # Write to the merged row 9 cell
            if len(doc.tables) > 1:
                table = doc.tables[1]
                if len(table.rows) > 9:
                    cell = table.rows[9].cells[0]
                    if cell.paragraphs:
                        para = cell.paragraphs[0]
                        para.clear()
                        para.add_run(combined_contact)
                    else:
                        cell.text = combined_contact

        # Fill each field
        for field_id, value in flat_data.items():
            # Skip contact fields as they were handled above
            if field_id in contact_fields:
                continue
            if field_id.startswith("_"):
                continue  # Skip system fields

            field_def = field_map.get(field_id)
            if not field_def:
                continue

            field_type = field_def.get("type", "text")

            # Handle checkbox fields specially
            if field_type == "checkbox" and isinstance(value, list):
                DocumentService._fill_checkbox_field(doc, value, field_def)
                continue

            anchor = field_def.get("anchor")
            if not anchor:
                continue

            DocumentService._write_value_to_anchor(doc, anchor, value, field_def)

        # Fix header table borders for LibreOffice compatibility
        # Table 0 Cell 0 (logo) should have no visible borders
        DocumentService._fix_header_table_borders(doc)

        # Save the filled document
        doc.save(output_path)
        
        return output_path

    @staticmethod
    def _fix_header_table_borders(doc: Document) -> None:
        """
        Fix header table (Table 0) borders for LibreOffice compatibility.
        Cell 0 (logo area) should have no visible borders.
        """
        from docx.oxml.ns import qn
        from docx.oxml import OxmlElement

        if len(doc.tables) == 0:
            return

        table = doc.tables[0]
        if len(table.rows) == 0:
            return

        # Fix Cell 0 (logo cell) - remove all borders
        cell = table.rows[0].cells[0]
        tc = cell._tc
        tc_pr = tc.get_or_add_tcPr()

        # Remove existing borders
        existing_borders = tc_pr.find(qn('w:tcBorders'))
        if existing_borders is not None:
            tc_pr.remove(existing_borders)

        # Add new borders element with all sides set to nil
        tc_borders = OxmlElement('w:tcBorders')
        for border_name in ['top', 'left', 'bottom', 'right']:
            border = OxmlElement(f'w:{border_name}')
            border.set(qn('w:val'), 'nil')
            tc_borders.append(border)
        tc_pr.append(tc_borders)

    @staticmethod
    def _fill_checkbox_field(
        doc: Document,
        selected_values: list,
        field_def: Dict[str, Any]
    ) -> None:
        """Fill checkbox fields by updating form field checkboxes or adding visual markers."""
        from docx.oxml.ns import qn

        options = field_def.get("options", [])

        # Build a map of option values to their labels
        option_labels = {opt.get("value"): opt.get("label", opt.get("value")) for opt in options}

        # Find paragraphs containing checkbox options and update them
        for para in doc.paragraphs:
            para_text = para.text.strip()

            # Check each option
            for opt_value, opt_label in option_labels.items():
                # Check if this paragraph contains this option's label
                if opt_label.lower() in para_text.lower():
                    is_selected = opt_value in selected_values

                    # Try to find and update form field checkboxes
                    for run in para.runs:
                        run_xml = run._r.xml
                        if 'fldChar' in run_xml or 'checkBox' in run_xml.lower():
                            # Found a form field - try to update it
                            for elem in run._r.iter():
                                # Look for checkbox default value
                                if elem.tag.endswith('default') or elem.tag.endswith('checked'):
                                    elem.set(qn('w:val'), '1' if is_selected else '0')

                    # Also try to find and replace checkbox symbols
                    # Common unchecked: ☐ (U+2610), □ (U+25A1)
                    # Common checked: ☑ (U+2611), ☒ (U+2612), ■ (U+25A0)
                    for run in para.runs:
                        if '☐' in run.text:
                            run.text = run.text.replace('☐', '☑' if is_selected else '☐')
                        elif '□' in run.text:
                            run.text = run.text.replace('□', '■' if is_selected else '□')

                    break  # Found the option, move to next

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
        
        # Find placeholder pattern (underscores, colon, question mark, or append)
        patterns = [
            (r'(_+)', formatted_value),  # Replace underscores
            (r'(:\s*)$', f': {formatted_value}'),  # Append after colon at end
            (r'(\?\s*)$', f'? {formatted_value}'),  # Append after question mark at end
        ]

        matched = False
        new_text = text
        for pattern, replacement in patterns:
            if re.search(pattern, text):
                new_text = re.sub(pattern, replacement, text, count=1)
                matched = True
                break

        # If no pattern matched, append the value at the end
        if not matched and formatted_value:
            new_text = f"{text.rstrip()} {formatted_value}"

        # Split text to separate original label from the filled value
        # so we can make only the value bold
        if matched:
            # Find where the value was inserted
            for pattern, replacement in patterns:
                match = re.search(pattern, text)
                if match:
                    prefix = text[:match.start()]
                    suffix = text[match.end():]
                    break
            else:
                prefix = text
                suffix = ""

            # Clear paragraph and add runs with formatting
            para.clear()
            if prefix:
                # Add space before value if prefix doesn't end with space
                if not prefix.endswith(' '):
                    prefix = prefix + ' '
                para.add_run(prefix)
            value_run = para.add_run(formatted_value)
            value_run.underline = True
            if suffix:
                para.add_run(suffix)
        else:
            # For appended values
            para.clear()
            para.add_run(text.rstrip() + "  ")  # Two spaces before value
            value_run = para.add_run(formatted_value)
            value_run.underline = True
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
        
        # Set cell text
        if cell.paragraphs:
            para = cell.paragraphs[0]
            para.clear()
            para.add_run(formatted_value)
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
        start_row = anchor.get("start_row", 1)  # Default to row 1 if not specified

        if table_index >= len(doc.tables):
            return

        table = doc.tables[table_index]
        repeatable_config = field_def.get("repeatable_config", {})
        columns = repeatable_config.get("columns", [])

        # Get column mapping - accounts for merged cells
        # Map logical column index to actual cell index
        column_mapping = repeatable_config.get("column_mapping", None)

        # Fill data rows starting from start_row
        for row_idx, row_data in enumerate(value):
            actual_row_idx = start_row + row_idx
            if actual_row_idx >= len(table.rows):
                # Need to add new row
                table.add_row()

            row = table.rows[actual_row_idx]

            for col_idx, col_def in enumerate(columns):
                # Use column_mapping if provided, otherwise use col_idx
                if column_mapping and col_idx < len(column_mapping):
                    actual_col_idx = column_mapping[col_idx]
                else:
                    actual_col_idx = col_idx

                if actual_col_idx >= len(row.cells):
                    continue

                cell = row.cells[actual_col_idx]
                col_id = col_def.get("id", f"col_{col_idx}")
                cell_value = row_data.get(col_id, "") if isinstance(row_data, dict) else ""

                if cell.paragraphs:
                    para = cell.paragraphs[0]
                    para.clear()
                    para.add_run(str(cell_value))
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
