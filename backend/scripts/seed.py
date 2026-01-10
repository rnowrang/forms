"""Seed script to create initial data for development/demo."""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.database import SessionLocal, engine, Base
from app.models.user import User, UserRole
from app.models.template import Template
from app.services.auth import AuthService

# Sample template schema for Minimal Risk IRB
MINIMAL_RISK_SCHEMA = {
    "sections": [
        {
            "id": "sec_I",
            "title": "I. Study Personnel",
            "description": "Information about the research team",
            "order": 0,
            "collapsible": True,
            "collapsed_by_default": False
        },
        {
            "id": "sec_II",
            "title": "II. Title and Funding",
            "description": "Protocol title and funding information",
            "order": 1,
            "collapsible": True,
            "collapsed_by_default": False
        },
        {
            "id": "sec_III",
            "title": "III. Research Purpose",
            "description": "Purpose and objectives of the research",
            "order": 2,
            "collapsible": True,
            "collapsed_by_default": False
        },
        {
            "id": "sec_IV",
            "title": "IV. Subject Population",
            "description": "Description of research subjects",
            "order": 3,
            "collapsible": True,
            "collapsed_by_default": True
        },
        {
            "id": "sec_V",
            "title": "V. Research Procedures",
            "description": "Methods and procedures",
            "order": 4,
            "collapsible": True,
            "collapsed_by_default": True
        },
        {
            "id": "sec_VI",
            "title": "VI. Data Security",
            "description": "Data handling and security measures",
            "order": 5,
            "collapsible": True,
            "collapsed_by_default": True
        }
    ],
    "fields": [
        # Section I - Study Personnel
        {
            "id": "personnel.pi_name",
            "type": "text",
            "label": "Principal Investigator Name",
            "section_id": "sec_I",
            "required": True,
            "placeholder": "Full name of PI",
            "order": 0,
            "anchor": {"type": "label", "label_text": "Principal Investigator"}
        },
        {
            "id": "personnel.pi_email",
            "type": "email",
            "label": "PI Email",
            "section_id": "sec_I",
            "required": True,
            "order": 1
        },
        {
            "id": "personnel.pi_phone",
            "type": "phone",
            "label": "PI Phone",
            "section_id": "sec_I",
            "required": True,
            "order": 2
        },
        {
            "id": "personnel.department",
            "type": "text",
            "label": "Department",
            "section_id": "sec_I",
            "required": True,
            "order": 3
        },
        {
            "id": "personnel.faculty_sponsor",
            "type": "text",
            "label": "Faculty Sponsor (if student)",
            "section_id": "sec_I",
            "required": False,
            "order": 4
        },
        
        # Section II - Title and Funding
        {
            "id": "study.title",
            "type": "text",
            "label": "Title of Protocol",
            "section_id": "sec_II",
            "required": True,
            "placeholder": "Enter the full title of your research protocol",
            "order": 0,
            "anchor": {"type": "label", "label_text": "TITLE OF PROTOCOL"}
        },
        {
            "id": "study.funding_source",
            "type": "select",
            "label": "Funding Source",
            "section_id": "sec_II",
            "required": True,
            "options": [
                {"value": "internal", "label": "Internal Funding"},
                {"value": "external_federal", "label": "External - Federal"},
                {"value": "external_private", "label": "External - Private"},
                {"value": "none", "label": "No Funding"},
                {"value": "other", "label": "Other"}
            ],
            "order": 1
        },
        {
            "id": "study.funding_source_other",
            "type": "text",
            "label": "Other Funding Source (specify)",
            "section_id": "sec_II",
            "required": False,
            "order": 2
        },
        {
            "id": "study.grant_number",
            "type": "text",
            "label": "Grant Number (if applicable)",
            "section_id": "sec_II",
            "required": False,
            "order": 3
        },
        
        # Section III - Research Purpose
        {
            "id": "purpose.summary",
            "type": "textarea",
            "label": "Brief Summary of Research",
            "section_id": "sec_III",
            "required": True,
            "help_text": "Provide a 1-2 paragraph summary of the research in lay terms",
            "order": 0
        },
        {
            "id": "purpose.objectives",
            "type": "textarea",
            "label": "Research Objectives",
            "section_id": "sec_III",
            "required": True,
            "order": 1
        },
        {
            "id": "purpose.hypothesis",
            "type": "textarea",
            "label": "Hypothesis (if applicable)",
            "section_id": "sec_III",
            "required": False,
            "order": 2
        },
        
        # Section IV - Subject Population
        {
            "id": "subjects.number",
            "type": "text",
            "label": "Number of Subjects",
            "section_id": "sec_IV",
            "required": True,
            "placeholder": "e.g., 100",
            "order": 0
        },
        {
            "id": "subjects.age_range",
            "type": "text",
            "label": "Age Range",
            "section_id": "sec_IV",
            "required": True,
            "placeholder": "e.g., 18-65",
            "order": 1
        },
        {
            "id": "subjects.includes_minors",
            "type": "radio",
            "label": "Will minors be included?",
            "section_id": "sec_IV",
            "required": True,
            "options": [
                {"value": "yes", "label": "Yes"},
                {"value": "no", "label": "No"}
            ],
            "order": 2
        },
        {
            "id": "subjects.vulnerable_populations",
            "type": "checkbox",
            "label": "Vulnerable Populations Included",
            "section_id": "sec_IV",
            "required": False,
            "options": [
                {"value": "prisoners", "label": "Prisoners"},
                {"value": "pregnant", "label": "Pregnant Women"},
                {"value": "cognitively_impaired", "label": "Cognitively Impaired"},
                {"value": "economically_disadvantaged", "label": "Economically Disadvantaged"},
                {"value": "none", "label": "None of the above"}
            ],
            "order": 3
        },
        {
            "id": "subjects.inclusion_criteria",
            "type": "textarea",
            "label": "Inclusion Criteria",
            "section_id": "sec_IV",
            "required": True,
            "order": 4
        },
        {
            "id": "subjects.exclusion_criteria",
            "type": "textarea",
            "label": "Exclusion Criteria",
            "section_id": "sec_IV",
            "required": True,
            "order": 5
        },
        
        # Section V - Research Procedures
        {
            "id": "procedures.description",
            "type": "textarea",
            "label": "Description of Procedures",
            "section_id": "sec_V",
            "required": True,
            "help_text": "Describe all procedures that subjects will undergo",
            "order": 0
        },
        {
            "id": "procedures.duration",
            "type": "text",
            "label": "Duration of Participation",
            "section_id": "sec_V",
            "required": True,
            "placeholder": "e.g., 1 hour, 3 sessions over 2 weeks",
            "order": 1
        },
        {
            "id": "procedures.location",
            "type": "text",
            "label": "Location of Research",
            "section_id": "sec_V",
            "required": True,
            "order": 2
        },
        {
            "id": "procedures.compensation",
            "type": "text",
            "label": "Compensation (if any)",
            "section_id": "sec_V",
            "required": False,
            "placeholder": "e.g., $20 gift card",
            "order": 3
        },
        
        # Section VI - Data Security
        {
            "id": "data.electronic_storage",
            "type": "radio",
            "label": "Will data be stored electronically?",
            "section_id": "sec_VI",
            "required": True,
            "options": [
                {"value": "yes", "label": "Yes"},
                {"value": "no", "label": "No"}
            ],
            "order": 0
        },
        {
            "id": "data.protections",
            "type": "checkbox",
            "label": "Data Protection Measures",
            "section_id": "sec_VI",
            "required": False,
            "options": [
                {"value": "encryption", "label": "Encryption"},
                {"value": "password", "label": "Password Protection"},
                {"value": "firewall", "label": "Firewall"},
                {"value": "physical_lock", "label": "Physical Lock/Security"},
                {"value": "deidentification", "label": "De-identification"}
            ],
            "order": 1
        },
        {
            "id": "data.retention_period",
            "type": "text",
            "label": "Data Retention Period",
            "section_id": "sec_VI",
            "required": True,
            "placeholder": "e.g., 5 years after study completion",
            "order": 2
        },
        {
            "id": "data.destruction_method",
            "type": "text",
            "label": "Data Destruction Method",
            "section_id": "sec_VI",
            "required": True,
            "order": 3
        }
    ],
    "rules": [
        {
            "id": "rule_funding_other",
            "conditions": [
                {"field": "study.funding_source", "operator": "equals", "value": "other"}
            ],
            "then_actions": [
                {"action": "show", "field": "study.funding_source_other"},
                {"action": "require", "field": "study.funding_source_other"}
            ],
            "else_actions": [
                {"action": "hide", "field": "study.funding_source_other"},
                {"action": "optional", "field": "study.funding_source_other"},
                {"action": "clear", "field": "study.funding_source_other"}
            ]
        },
        {
            "id": "rule_electronic_data",
            "conditions": [
                {"field": "data.electronic_storage", "operator": "equals", "value": "yes"}
            ],
            "then_actions": [
                {"action": "show", "field": "data.protections"},
                {"action": "require", "field": "data.protections"}
            ],
            "else_actions": [
                {"action": "hide", "field": "data.protections"},
                {"action": "optional", "field": "data.protections"}
            ]
        }
    ]
}


def seed_database():
    """Create initial seed data."""
    db = SessionLocal()
    
    try:
        # Create users
        print("Creating users...")
        
        # Admin user
        admin = db.query(User).filter(User.email == "admin@example.com").first()
        if not admin:
            admin = User(
                email="admin@example.com",
                hashed_password=AuthService.get_password_hash("admin123"),
                full_name="Admin User",
                role=UserRole.ADMIN,
            )
            db.add(admin)
            print("  Created admin user: admin@example.com / admin123")
        
        # Reviewer user
        reviewer = db.query(User).filter(User.email == "reviewer@example.com").first()
        if not reviewer:
            reviewer = User(
                email="reviewer@example.com",
                hashed_password=AuthService.get_password_hash("reviewer123"),
                full_name="Jane Reviewer",
                role=UserRole.REVIEWER,
            )
            db.add(reviewer)
            print("  Created reviewer user: reviewer@example.com / reviewer123")
        
        # Researcher user
        researcher = db.query(User).filter(User.email == "researcher@example.com").first()
        if not researcher:
            researcher = User(
                email="researcher@example.com",
                hashed_password=AuthService.get_password_hash("researcher123"),
                full_name="John Researcher",
                role=UserRole.RESEARCHER,
            )
            db.add(researcher)
            print("  Created researcher user: researcher@example.com / researcher123")
        
        db.commit()
        
        # Create sample template
        print("\nCreating templates...")
        
        template = db.query(Template).filter(Template.name == "Minimal Risk IRB Application").first()
        if not template:
            template = Template(
                name="Minimal Risk IRB Application",
                description="Application for research involving minimal risk to participants. Use this form for surveys, interviews, and observational studies.",
                version="1.0",
                original_file_path="/app/storage/templates/minimal_risk_template.docx",
                original_file_name="irb-application-minimal-risk.docx",
                schema=MINIMAL_RISK_SCHEMA,
                is_active=True,
                is_published=True,
            )
            db.add(template)
            print("  Created template: Minimal Risk IRB Application")
        
        db.commit()
        
        print("\nSeed data created successfully!")
        print("\nYou can now log in with:")
        print("  Admin:      admin@example.com / admin123")
        print("  Reviewer:   reviewer@example.com / reviewer123")
        print("  Researcher: researcher@example.com / researcher123")
        
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    # Create tables
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    
    # Seed data
    seed_database()
