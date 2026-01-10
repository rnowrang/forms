"""Initial database schema

Revision ID: 001
Revises: 
Create Date: 2024-01-01

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Users table
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('hashed_password', sa.String(255), nullable=False),
        sa.Column('full_name', sa.String(255), nullable=False),
        sa.Column('role', sa.Enum('admin', 'researcher', 'reviewer', name='userrole'), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=True, default=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_users_id', 'users', ['id'])
    op.create_index('ix_users_email', 'users', ['email'], unique=True)
    
    # Templates table
    op.create_table(
        'templates',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('version', sa.String(50), nullable=True, default='1.0'),
        sa.Column('original_file_path', sa.String(512), nullable=False),
        sa.Column('original_file_name', sa.String(255), nullable=False),
        sa.Column('schema', sa.JSON(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=True, default=True),
        sa.Column('is_published', sa.Boolean(), nullable=True, default=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_templates_id', 'templates', ['id'])
    
    # Form instances table
    op.create_table(
        'form_instances',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('template_id', sa.Integer(), nullable=False),
        sa.Column('owner_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(512), nullable=False),
        sa.Column('status', sa.Enum('draft', 'in_review', 'needs_changes', 'approved', 'locked', name='formstatus'), nullable=False),
        sa.Column('current_version_number', sa.Integer(), nullable=True, default=1),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('submitted_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['template_id'], ['templates.id']),
        sa.ForeignKeyConstraint(['owner_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_form_instances_id', 'form_instances', ['id'])
    op.create_index('ix_form_instances_template_id', 'form_instances', ['template_id'])
    op.create_index('ix_form_instances_owner_id', 'form_instances', ['owner_id'])
    op.create_index('ix_form_instances_status', 'form_instances', ['status'])
    
    # Form versions table
    op.create_table(
        'form_versions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('form_instance_id', sa.Integer(), nullable=False),
        sa.Column('version_number', sa.Integer(), nullable=False),
        sa.Column('version_label', sa.String(100), nullable=True),
        sa.Column('data_snapshot', sa.JSON(), nullable=False),
        sa.Column('status_at_creation', sa.Enum('draft', 'in_review', 'needs_changes', 'approved', 'locked', name='formstatus', create_type=False), nullable=False),
        sa.Column('generated_docx_path', sa.String(512), nullable=True),
        sa.Column('generated_pdf_path', sa.String(512), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('created_by_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['form_instance_id'], ['form_instances.id']),
        sa.ForeignKeyConstraint(['created_by_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_form_versions_id', 'form_versions', ['id'])
    op.create_index('ix_form_versions_form_instance_id', 'form_versions', ['form_instance_id'])
    
    # Form data table (current working data)
    op.create_table(
        'form_data',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('form_instance_id', sa.Integer(), nullable=False),
        sa.Column('data', sa.JSON(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['form_instance_id'], ['form_instances.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('form_instance_id')
    )
    op.create_index('ix_form_data_id', 'form_data', ['id'])
    op.create_index('ix_form_data_form_instance_id', 'form_data', ['form_instance_id'])
    
    # Change events table (audit trail)
    op.create_table(
        'change_events',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('form_instance_id', sa.Integer(), nullable=False),
        sa.Column('version_id', sa.Integer(), nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('field_id', sa.String(255), nullable=False),
        sa.Column('field_label', sa.String(512), nullable=True),
        sa.Column('old_value', sa.JSON(), nullable=True),
        sa.Column('new_value', sa.JSON(), nullable=True),
        sa.Column('action_type', sa.String(50), nullable=True),
        sa.Column('action_details', sa.Text(), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.String(512), nullable=True),
        sa.ForeignKeyConstraint(['form_instance_id'], ['form_instances.id']),
        sa.ForeignKeyConstraint(['version_id'], ['form_versions.id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_change_events_id', 'change_events', ['id'])
    op.create_index('ix_change_events_form_instance_id', 'change_events', ['form_instance_id'])
    op.create_index('ix_change_events_version_id', 'change_events', ['version_id'])
    op.create_index('ix_change_events_user_id', 'change_events', ['user_id'])
    op.create_index('ix_change_events_field_id', 'change_events', ['field_id'])
    
    # Comment threads table
    op.create_table(
        'comment_threads',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('form_instance_id', sa.Integer(), nullable=False),
        sa.Column('field_id', sa.String(255), nullable=True),
        sa.Column('section_id', sa.String(255), nullable=True),
        sa.Column('is_resolved', sa.Boolean(), nullable=True, default=False),
        sa.Column('resolved_at', sa.DateTime(), nullable=True),
        sa.Column('resolved_by_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['form_instance_id'], ['form_instances.id']),
        sa.ForeignKeyConstraint(['resolved_by_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_comment_threads_id', 'comment_threads', ['id'])
    op.create_index('ix_comment_threads_form_instance_id', 'comment_threads', ['form_instance_id'])
    op.create_index('ix_comment_threads_field_id', 'comment_threads', ['field_id'])
    
    # Comments table
    op.create_table(
        'comments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('thread_id', sa.Integer(), nullable=False),
        sa.Column('author_id', sa.Integer(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('is_deleted', sa.Boolean(), nullable=True, default=False),
        sa.ForeignKeyConstraint(['thread_id'], ['comment_threads.id']),
        sa.ForeignKeyConstraint(['author_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_comments_id', 'comments', ['id'])
    op.create_index('ix_comments_thread_id', 'comments', ['thread_id'])
    op.create_index('ix_comments_author_id', 'comments', ['author_id'])
    
    # Review actions table
    op.create_table(
        'review_actions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('form_instance_id', sa.Integer(), nullable=False),
        sa.Column('version_id', sa.Integer(), nullable=False),
        sa.Column('performed_by_id', sa.Integer(), nullable=False),
        sa.Column('action_type', sa.Enum('submit_for_review', 'request_changes', 'approve', 'reject', 'return_to_draft', name='reviewactiontype'), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['form_instance_id'], ['form_instances.id']),
        sa.ForeignKeyConstraint(['version_id'], ['form_versions.id']),
        sa.ForeignKeyConstraint(['performed_by_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_review_actions_id', 'review_actions', ['id'])
    op.create_index('ix_review_actions_form_instance_id', 'review_actions', ['form_instance_id'])
    op.create_index('ix_review_actions_version_id', 'review_actions', ['version_id'])
    op.create_index('ix_review_actions_performed_by_id', 'review_actions', ['performed_by_id'])


def downgrade() -> None:
    op.drop_table('review_actions')
    op.drop_table('comments')
    op.drop_table('comment_threads')
    op.drop_table('change_events')
    op.drop_table('form_data')
    op.drop_table('form_versions')
    op.drop_table('form_instances')
    op.drop_table('templates')
    op.drop_table('users')
    
    # Drop enums
    op.execute("DROP TYPE IF EXISTS reviewactiontype")
    op.execute("DROP TYPE IF EXISTS formstatus")
    op.execute("DROP TYPE IF EXISTS userrole")
