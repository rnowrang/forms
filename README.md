# IRB Forms Management System

A comprehensive web application for managing IRB (Institutional Review Board) applications with smart online forms, conditional logic, versioning, review workflows, and pixel-faithful document generation.

## Features

### Core Features
- **Template Ingestion**: Upload DOCX templates and automatically extract form schemas with semantic anchoring
- **Smart Web Forms**: Dynamic forms with collapsible sections, conditional logic, and repeatable groups
- **Version Control**: Full versioning with audit trails and change tracking
- **Review Workflow**: Complete workflow with states (Draft → In Review → Needs Changes → Approved → Locked)
- **Document Generation**: Generate filled DOCX and PDF documents that preserve original formatting

### User Roles
- **Researcher**: Create and submit IRB applications
- **Reviewer**: Review submissions, request changes, approve/reject
- **Admin**: Manage templates, users, and system configuration

## Tech Stack

### Backend
- Python 3.11 with FastAPI
- PostgreSQL with SQLAlchemy ORM
- Alembic for database migrations
- python-docx for document processing
- LibreOffice (headless) for PDF conversion

### Frontend
- React 18 with TypeScript
- Vite for build tooling
- TailwindCSS for styling
- React Query for data fetching
- React Hook Form with Zod validation
- Zustand for state management

## Quick Start

### Prerequisites
- Docker and Docker Compose
- (Optional) Node.js 20+ and Python 3.11+ for local development

### Using Docker (Recommended)

1. Clone the repository and navigate to the project directory:
```bash
cd forms
```

2. Copy the environment file:
```bash
cp env.example .env
```

3. Start all services:
```bash
docker-compose up -d
```

4. Run database migrations:
```bash
docker-compose exec backend alembic upgrade head
```

5. Seed the database with sample data:
```bash
docker-compose exec backend python scripts/seed.py
```

6. Access the application:
   - Frontend: http://localhost:5173
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

### Default Users

After seeding, you can log in with:

| Role | Email | Password |
|------|-------|----------|
| Admin | admin@example.com | admin123 |
| Reviewer | reviewer@example.com | reviewer123 |
| Researcher | researcher@example.com | researcher123 |

## Development

### Backend Development

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run migrations
alembic upgrade head

# Start development server
uvicorn app.main:app --reload --port 8000
```

### Frontend Development

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

## Project Structure

```
forms/
├── backend/
│   ├── app/
│   │   ├── models/          # SQLAlchemy models
│   │   ├── routers/         # API endpoints
│   │   ├── schemas/         # Pydantic schemas
│   │   ├── services/        # Business logic
│   │   ├── config.py        # Configuration
│   │   ├── database.py      # Database setup
│   │   └── main.py          # FastAPI application
│   ├── alembic/             # Database migrations
│   ├── scripts/             # Utility scripts
│   ├── Dockerfile.dev
│   ├── Dockerfile.prod
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/      # React components
│   │   ├── pages/           # Page components
│   │   ├── lib/             # API client
│   │   ├── stores/          # Zustand stores
│   │   ├── types/           # TypeScript types
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── Dockerfile.dev
│   ├── Dockerfile.prod
│   └── package.json
├── storage/                  # File storage (gitignored)
│   ├── uploads/
│   ├── generated/
│   └── templates/
├── docker-compose.yml
├── docker-compose.prod.yml
└── README.md
```

## API Endpoints

### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login (form data)
- `POST /api/auth/login/json` - Login (JSON)
- `GET /api/auth/me` - Get current user

### Templates
- `GET /api/templates` - List all templates
- `GET /api/templates/published` - List published templates
- `GET /api/templates/{id}` - Get template details
- `POST /api/templates` - Upload new template (admin)
- `PUT /api/templates/{id}` - Update template (admin)
- `POST /api/templates/{id}/publish` - Publish template (admin)

### Forms
- `GET /api/forms` - List user's forms
- `POST /api/forms` - Create new form
- `GET /api/forms/{id}` - Get form details
- `POST /api/forms/{id}/data` - Update form data (autosave)
- `DELETE /api/forms/{id}` - Delete draft form

### Versions
- `GET /api/versions/form/{form_id}` - List form versions
- `POST /api/versions/form/{form_id}` - Create new version
- `GET /api/versions/{id}` - Get version details

### Review
- `POST /api/review/form/{id}/submit` - Submit for review
- `POST /api/review/form/{id}/request-changes` - Request changes
- `POST /api/review/form/{id}/approve` - Approve form
- `GET /api/review/form/{id}/comments` - Get comments
- `POST /api/review/form/{id}/comments` - Add comment

### Export
- `POST /api/export/form/{id}/generate` - Generate documents
- `GET /api/export/form/{id}/docx` - Download DOCX
- `GET /api/export/form/{id}/pdf` - Download PDF

### Audit
- `GET /api/audit/form/{id}` - Get audit log
- `GET /api/audit/form/{id}/summary` - Get activity summary

## Template Schema Format

Templates use a JSON schema format:

```json
{
  "sections": [
    {
      "id": "sec_I",
      "title": "I. Study Personnel",
      "order": 0,
      "collapsible": true
    }
  ],
  "fields": [
    {
      "id": "study.title",
      "type": "text",
      "label": "Title of Protocol",
      "section_id": "sec_I",
      "required": true,
      "anchor": {
        "type": "label",
        "label_text": "TITLE OF PROTOCOL"
      }
    }
  ],
  "rules": [
    {
      "id": "rule_other",
      "conditions": [
        {"field": "funding", "operator": "equals", "value": "other"}
      ],
      "then_actions": [
        {"action": "show", "field": "funding_other"}
      ],
      "else_actions": [
        {"action": "hide", "field": "funding_other"}
      ]
    }
  ]
}
```

### Field Types
- `text` - Single line text input
- `textarea` - Multi-line text
- `email` - Email input
- `phone` - Phone number
- `date` - Date picker
- `select` - Dropdown select
- `radio` - Radio button group
- `checkbox` - Checkbox group
- `repeatable` - Repeatable row group

### Anchor Types
- `label` - Anchor by nearby label text
- `paragraph` - Anchor by paragraph content
- `table_cell` - Anchor by table cell position
- `table` - Anchor for repeatable tables

## LibreOffice PDF Conversion

The system uses LibreOffice in headless mode for PDF conversion. This is automatically installed in the Docker container.

For local development, install LibreOffice:

```bash
# Ubuntu/Debian
sudo apt install libreoffice

# macOS
brew install libreoffice

# Windows
# Download from https://www.libreoffice.org/download/download/
```

## Production Deployment

1. Update environment variables in `.env` with production values
2. Build and run with production compose file:

```bash
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests
5. Submit a pull request

## License

MIT License - see LICENSE file for details
