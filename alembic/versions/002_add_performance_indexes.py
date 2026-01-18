"""Add performance indexes.

Revision ID: 002
Revises: 001
Create Date: 2024-01-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Users table indexes
    op.create_index("ix_users_family_id", "users", ["family_id"])
    op.create_index("ix_users_email_verified", "users", ["email_verified"])

    # Children table indexes
    op.create_index("ix_children_family_id", "children", ["family_id"])
    op.create_index("ix_children_family_active", "children", ["family_id", "is_active"])

    # Chat sessions indexes
    op.create_index("ix_chat_sessions_family_id", "chat_sessions", ["family_id"])
    op.create_index("ix_chat_sessions_child_id", "chat_sessions", ["child_id"])
    op.create_index("ix_chat_sessions_created", "chat_sessions", ["created_at"])

    # Chat messages indexes
    op.create_index("ix_chat_messages_session_id", "chat_messages", ["session_id"])

    # Milestones indexes
    op.create_index("ix_milestones_age_stage_id", "milestones", ["age_stage_id"])
    op.create_index("ix_milestones_domain_id", "milestones", ["domain_id"])
    op.create_index("ix_milestones_active", "milestones", ["is_active"])
    op.create_index(
        "ix_milestones_stage_domain",
        "milestones",
        ["age_stage_id", "domain_id", "is_active"],
    )

    # Activities indexes
    op.create_index("ix_activities_age_stage_id", "activities", ["age_stage_id"])
    op.create_index("ix_activities_domain_id", "activities", ["domain_id"])
    op.create_index("ix_activities_active", "activities", ["is_active"])
    op.create_index(
        "ix_activities_stage_domain",
        "activities",
        ["age_stage_id", "domain_id", "is_active"],
    )

    # Child progress indexes
    op.create_index("ix_child_progress_child_id", "child_progress", ["child_id"])
    op.create_index("ix_child_progress_milestone_id", "child_progress", ["milestone_id"])
    op.create_index("ix_child_progress_activity_id", "child_progress", ["activity_id"])
    op.create_index("ix_child_progress_status", "child_progress", ["status"])
    op.create_index(
        "ix_child_progress_child_status",
        "child_progress",
        ["child_id", "status"],
    )

    # Resources indexes
    op.create_index("ix_resources_type", "resources", ["resource_type"])
    op.create_index("ix_resources_featured", "resources", ["is_featured"])
    op.create_index("ix_resources_created", "resources", ["created_at"])

    # Bookmarks indexes
    op.create_index("ix_bookmarks_user_id", "bookmarks", ["user_id"])
    op.create_index("ix_bookmarks_resource_id", "bookmarks", ["resource_id"])

    # Age stages indexes
    op.create_index("ix_age_stages_order", "age_stages", ["order"])
    op.create_index("ix_age_stages_age_range", "age_stages", ["min_age_months", "max_age_months"])


def downgrade() -> None:
    # Drop all indexes in reverse order
    op.drop_index("ix_age_stages_age_range", table_name="age_stages")
    op.drop_index("ix_age_stages_order", table_name="age_stages")

    op.drop_index("ix_bookmarks_resource_id", table_name="bookmarks")
    op.drop_index("ix_bookmarks_user_id", table_name="bookmarks")

    op.drop_index("ix_resources_created", table_name="resources")
    op.drop_index("ix_resources_featured", table_name="resources")
    op.drop_index("ix_resources_type", table_name="resources")

    op.drop_index("ix_child_progress_child_status", table_name="child_progress")
    op.drop_index("ix_child_progress_status", table_name="child_progress")
    op.drop_index("ix_child_progress_activity_id", table_name="child_progress")
    op.drop_index("ix_child_progress_milestone_id", table_name="child_progress")
    op.drop_index("ix_child_progress_child_id", table_name="child_progress")

    op.drop_index("ix_activities_stage_domain", table_name="activities")
    op.drop_index("ix_activities_active", table_name="activities")
    op.drop_index("ix_activities_domain_id", table_name="activities")
    op.drop_index("ix_activities_age_stage_id", table_name="activities")

    op.drop_index("ix_milestones_stage_domain", table_name="milestones")
    op.drop_index("ix_milestones_active", table_name="milestones")
    op.drop_index("ix_milestones_domain_id", table_name="milestones")
    op.drop_index("ix_milestones_age_stage_id", table_name="milestones")

    op.drop_index("ix_chat_messages_session_id", table_name="chat_messages")

    op.drop_index("ix_chat_sessions_created", table_name="chat_sessions")
    op.drop_index("ix_chat_sessions_child_id", table_name="chat_sessions")
    op.drop_index("ix_chat_sessions_family_id", table_name="chat_sessions")

    op.drop_index("ix_children_family_active", table_name="children")
    op.drop_index("ix_children_family_id", table_name="children")

    op.drop_index("ix_users_email_verified", table_name="users")
    op.drop_index("ix_users_family_id", table_name="users")
