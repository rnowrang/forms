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

# Load schema from JSON file
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SCHEMA_FILE = os.path.join(SCRIPT_DIR, 'irb_anonymous_survey_schema.json')

def load_schema():
    """Load template schema from JSON file."""
    if os.path.exists(SCHEMA_FILE):
        with open(SCHEMA_FILE, 'r') as f:
            return json.load(f)
    else:
        print(f"Warning: Schema file not found at {SCHEMA_FILE}")
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

        # Create IRB Anonymous Survey template
        print("\nCreating templates...")

        schema = load_schema()

        template = db.query(Template).filter(Template.name == "IRB Application for Anonymous Survey").first()
        if not template:
            template = Template(
                name="IRB Application for Anonymous Survey",
                description="Application for research involving anonymous surveys. Use this form for anonymous survey-based studies with minimal risk.",
                version="1.0",
                original_file_path="/app/storage/templates/IRB_v6.docx",
                original_file_name="IRB_v6.docx",
                schema=schema,
                is_active=True,
                is_published=True,
            )
            db.add(template)
            print("  Created template: IRB Application for Anonymous Survey")
        else:
            # Update existing template with latest schema
            template.schema = schema
            template.original_file_path = "/app/storage/templates/IRB_v6.docx"
            print("  Updated template: IRB Application for Anonymous Survey")

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
