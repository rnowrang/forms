"""Seed script to create initial data for development/demo."""

import sys
import os
import json

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.database import SessionLocal, engine, Base
from app.models.user import User, UserRole
from app.models.template import Template
from app.services.auth import AuthService

# Schema files directory
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Template configurations
TEMPLATES = [
    {
        "name": "IRB Application for Anonymous Survey",
        "description": "Application for research involving anonymous surveys. Use this form for anonymous survey-based studies with minimal risk.",
        "version": "1.0",
        "schema_file": "irb_anonymous_survey_schema.json",
        "template_file": "IRB_v6.docx",
        "original_file_name": "IRB_v6.docx"
    },
    {
        "name": "IRB Application for Archival/Retrospective Research",
        "description": "Application for research using existing archived or retrospective data. Use this form for studies that analyze existing records, medical charts, or historical data without direct subject interaction.",
        "version": "1.0",
        "schema_file": "irb_archival_retrospective_schema.json",
        "template_file": "irb-application-archival-retrospective 6_6_25.docx",
        "original_file_name": "irb-application-archival-retrospective 6_6_25.docx"
    },
    {
        "name": "IRB Application for Minimal Risk Studies",
        "description": "Application for minimal risk research studies. Use this form for studies that pose no more than minimal risk to subjects, including surveys, interviews, observational studies, and non-invasive procedures.",
        "version": "1.0",
        "schema_file": "irb_minimal_risk_schema.json",
        "template_file": "irb-application-minimal-risk 11.1.2024 (1).docx",
        "original_file_name": "irb-application-minimal-risk 11.1.2024 (1).docx"
    },
    {
        "name": "IRB Application - Standard",
        "description": "Standard IRB application for research studies. Use this comprehensive form for studies involving drugs, biologics, devices, greater than minimal risk procedures, or complex research protocols.",
        "version": "1.0",
        "schema_file": "irb_standard_schema.json",
        "template_file": "irb-application-standard 1_21_2019 (1).docx",
        "original_file_name": "irb-application-standard 1_21_2019 (1).docx"
    }
]


def load_schema(schema_file):
    """Load template schema from JSON file."""
    schema_path = os.path.join(SCRIPT_DIR, schema_file)
    if os.path.exists(schema_path):
        with open(schema_path, 'r') as f:
            return json.load(f)
    else:
        print(f"Warning: Schema file not found at {schema_path}")
        return {"sections": [], "fields": [], "rules": []}


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

        # Create all IRB templates
        print("\nCreating templates...")

        for template_config in TEMPLATES:
            schema = load_schema(template_config["schema_file"])
            template_path = f"/app/storage/templates/{template_config['template_file']}"

            template = db.query(Template).filter(Template.name == template_config["name"]).first()
            if not template:
                template = Template(
                    name=template_config["name"],
                    description=template_config["description"],
                    version=template_config["version"],
                    original_file_path=template_path,
                    original_file_name=template_config["original_file_name"],
                    schema=schema,
                    is_active=True,
                    is_published=True,
                )
                db.add(template)
                print(f"  Created template: {template_config['name']}")
            else:
                # Update existing template with latest schema
                template.schema = schema
                template.original_file_path = template_path
                template.description = template_config["description"]
                print(f"  Updated template: {template_config['name']}")

        db.commit()

        print("\nSeed data created successfully!")
        print(f"\nCreated {len(TEMPLATES)} templates:")
        for t in TEMPLATES:
            print(f"  - {t['name']}")
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
