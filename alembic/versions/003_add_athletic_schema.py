"""Add athletic schema for Student-Athlete Curriculum.

Revision ID: 003
Revises: 002
Create Date: 2026-01-13 15:10:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Sports table
    op.create_table(
        "sports",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("slug", sa.String(length=50), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("icon", sa.String(length=50), nullable=True),
        sa.Column("color", sa.String(length=20), nullable=True),
        sa.Column("is_team_sport", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("has_positions", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("season_type", sa.String(length=20), nullable=False, server_default="year-round"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug"),
    )
    op.create_index("ix_sports_slug", "sports", ["slug"])

    # Athletic Age Stages (LTAD model)
    op.create_table(
        "athletic_age_stages",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("slug", sa.String(length=50), nullable=False),
        sa.Column("min_age_months", sa.Integer(), nullable=False),
        sa.Column("max_age_months", sa.Integer(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("ltad_stage", sa.String(length=50), nullable=False),
        sa.Column("focus_areas", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("order", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug"),
    )
    op.create_index("ix_athletic_age_stages_order", "athletic_age_stages", ["order"])
    op.create_index("ix_athletic_age_stages_age_range", "athletic_age_stages", ["min_age_months", "max_age_months"])

    # Athletic Domains
    op.create_table(
        "athletic_domains",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("slug", sa.String(length=50), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("icon", sa.String(length=50), nullable=True),
        sa.Column("color", sa.String(length=20), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug"),
    )

    # Athletic Milestones
    op.create_table(
        "athletic_milestones",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("sport_id", sa.UUID(), nullable=True),
        sa.Column("athletic_age_stage_id", sa.UUID(), nullable=False),
        sa.Column("athletic_domain_id", sa.UUID(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("typical_age_months", sa.Integer(), nullable=True),
        sa.Column("importance", sa.String(length=20), nullable=False, server_default="normal"),
        sa.Column("source", sa.String(length=255), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.ForeignKeyConstraint(["sport_id"], ["sports.id"]),
        sa.ForeignKeyConstraint(["athletic_age_stage_id"], ["athletic_age_stages.id"]),
        sa.ForeignKeyConstraint(["athletic_domain_id"], ["athletic_domains.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_athletic_milestones_sport_id", "athletic_milestones", ["sport_id"])
    op.create_index("ix_athletic_milestones_age_stage_id", "athletic_milestones", ["athletic_age_stage_id"])
    op.create_index("ix_athletic_milestones_domain_id", "athletic_milestones", ["athletic_domain_id"])
    op.create_index("ix_athletic_milestones_active", "athletic_milestones", ["is_active"])

    # Athletes (profile linked to children)
    op.create_table(
        "athletes",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("child_id", sa.UUID(), nullable=False),
        sa.Column("primary_sport_id", sa.UUID(), nullable=True),
        sa.Column("secondary_sports", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("position", sa.String(length=100), nullable=True),
        sa.Column("height_inches", sa.Integer(), nullable=True),
        sa.Column("weight_lbs", sa.Integer(), nullable=True),
        sa.Column("dominant_hand", sa.String(length=10), nullable=True),
        sa.Column("club_team", sa.String(length=255), nullable=True),
        sa.Column("school_team", sa.String(length=255), nullable=True),
        sa.Column("jersey_number", sa.String(length=10), nullable=True),
        sa.Column("recruitment_status", sa.String(length=50), nullable=False, server_default="not_started"),
        sa.Column("target_division", sa.String(length=20), nullable=True),
        sa.Column("graduation_year", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["child_id"], ["children.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["primary_sport_id"], ["sports.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("child_id"),
    )
    op.create_index("ix_athletes_child_id", "athletes", ["child_id"])
    op.create_index("ix_athletes_primary_sport_id", "athletes", ["primary_sport_id"])
    op.create_index("ix_athletes_recruitment_status", "athletes", ["recruitment_status"])

    # Academic Records
    op.create_table(
        "academic_records",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("athlete_id", sa.UUID(), nullable=False),
        sa.Column("record_type", sa.String(length=30), nullable=False),
        sa.Column("semester", sa.String(length=50), nullable=True),
        sa.Column("grade_level", sa.Integer(), nullable=True),
        sa.Column("gpa", sa.Float(), nullable=True),
        sa.Column("cumulative_gpa", sa.Float(), nullable=True),
        sa.Column("core_gpa", sa.Float(), nullable=True),
        sa.Column("test_type", sa.String(length=20), nullable=True),
        sa.Column("test_score", sa.Integer(), nullable=True),
        sa.Column("test_date", sa.Date(), nullable=True),
        sa.Column("course_name", sa.String(length=255), nullable=True),
        sa.Column("course_type", sa.String(length=30), nullable=True),
        sa.Column("credits", sa.Float(), nullable=True),
        sa.Column("grade", sa.String(length=5), nullable=True),
        sa.Column("is_ncaa_approved", sa.Boolean(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["athlete_id"], ["athletes.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_academic_records_athlete_id", "academic_records", ["athlete_id"])
    op.create_index("ix_academic_records_record_type", "academic_records", ["record_type"])

    # Training Plans
    op.create_table(
        "training_plans",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("sport_id", sa.UUID(), nullable=True),
        sa.Column("athletic_age_stage_id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("duration_weeks", sa.Integer(), nullable=False),
        sa.Column("sessions_per_week", sa.Integer(), nullable=False),
        sa.Column("focus", sa.String(length=30), nullable=False, server_default="hybrid"),
        sa.Column("difficulty", sa.String(length=20), nullable=False, server_default="beginner"),
        sa.Column("equipment_needed", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("source", sa.String(length=255), nullable=True),
        sa.Column("is_template", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["sport_id"], ["sports.id"]),
        sa.ForeignKeyConstraint(["athletic_age_stage_id"], ["athletic_age_stages.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_training_plans_sport_id", "training_plans", ["sport_id"])
    op.create_index("ix_training_plans_age_stage_id", "training_plans", ["athletic_age_stage_id"])
    op.create_index("ix_training_plans_is_template", "training_plans", ["is_template"])

    # Training Sessions
    op.create_table(
        "training_sessions",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("training_plan_id", sa.UUID(), nullable=False),
        sa.Column("week_number", sa.Integer(), nullable=False),
        sa.Column("day_of_week", sa.Integer(), nullable=False),
        sa.Column("session_type", sa.String(length=30), nullable=False, server_default="skills"),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("duration_minutes", sa.Integer(), nullable=False),
        sa.Column("warmup", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("main_workout", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("cooldown", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("order", sa.Integer(), nullable=False, server_default="0"),
        sa.ForeignKeyConstraint(["training_plan_id"], ["training_plans.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_training_sessions_plan_id", "training_sessions", ["training_plan_id"])
    op.create_index("ix_training_sessions_week_day", "training_sessions", ["week_number", "day_of_week"])

    # Athlete Training Plan Assignments
    op.create_table(
        "athlete_training_plans",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("athlete_id", sa.UUID(), nullable=False),
        sa.Column("training_plan_id", sa.UUID(), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="active"),
        sa.Column("current_week", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["athlete_id"], ["athletes.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["training_plan_id"], ["training_plans.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_athlete_training_plans_athlete_id", "athlete_training_plans", ["athlete_id"])
    op.create_index("ix_athlete_training_plans_status", "athlete_training_plans", ["status"])

    # Training Progress
    op.create_table(
        "training_progress",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("athlete_id", sa.UUID(), nullable=False),
        sa.Column("training_session_id", sa.UUID(), nullable=False),
        sa.Column("athlete_training_plan_id", sa.UUID(), nullable=False),
        sa.Column("scheduled_date", sa.Date(), nullable=False),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="scheduled"),
        sa.Column("actual_duration_minutes", sa.Integer(), nullable=True),
        sa.Column("difficulty_rating", sa.Integer(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("modifications", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["athlete_id"], ["athletes.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["training_session_id"], ["training_sessions.id"]),
        sa.ForeignKeyConstraint(["athlete_training_plan_id"], ["athlete_training_plans.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_training_progress_athlete_id", "training_progress", ["athlete_id"])
    op.create_index("ix_training_progress_session_id", "training_progress", ["training_session_id"])
    op.create_index("ix_training_progress_status", "training_progress", ["status"])
    op.create_index("ix_training_progress_scheduled", "training_progress", ["scheduled_date"])

    # Recruitment Contacts
    op.create_table(
        "recruitment_contacts",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("athlete_id", sa.UUID(), nullable=False),
        sa.Column("college_name", sa.String(length=255), nullable=False),
        sa.Column("division", sa.String(length=20), nullable=False),
        sa.Column("conference", sa.String(length=100), nullable=True),
        sa.Column("coach_name", sa.String(length=255), nullable=True),
        sa.Column("coach_title", sa.String(length=100), nullable=True),
        sa.Column("coach_email", sa.String(length=255), nullable=True),
        sa.Column("coach_phone", sa.String(length=50), nullable=True),
        sa.Column("interest_level", sa.String(length=30), nullable=False, server_default="researching"),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="researching"),
        sa.Column("last_contact_date", sa.Date(), nullable=True),
        sa.Column("next_action", sa.String(length=255), nullable=True),
        sa.Column("next_action_date", sa.Date(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["athlete_id"], ["athletes.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_recruitment_contacts_athlete_id", "recruitment_contacts", ["athlete_id"])
    op.create_index("ix_recruitment_contacts_status", "recruitment_contacts", ["status"])
    op.create_index("ix_recruitment_contacts_division", "recruitment_contacts", ["division"])

    # Recruitment Events
    op.create_table(
        "recruitment_events",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("athlete_id", sa.UUID(), nullable=False),
        sa.Column("recruitment_contact_id", sa.UUID(), nullable=True),
        sa.Column("event_type", sa.String(length=50), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("location", sa.String(length=255), nullable=True),
        sa.Column("event_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column("cost", sa.Float(), nullable=True),
        sa.Column("registration_deadline", sa.Date(), nullable=True),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="planned"),
        sa.Column("outcome", sa.Text(), nullable=True),
        sa.Column("contacts_made", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["athlete_id"], ["athletes.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["recruitment_contact_id"], ["recruitment_contacts.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_recruitment_events_athlete_id", "recruitment_events", ["athlete_id"])
    op.create_index("ix_recruitment_events_event_date", "recruitment_events", ["event_date"])
    op.create_index("ix_recruitment_events_status", "recruitment_events", ["status"])

    # Athletic Progress
    op.create_table(
        "athletic_progress",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("athlete_id", sa.UUID(), nullable=False),
        sa.Column("athletic_milestone_id", sa.UUID(), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="not_started"),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("video_url", sa.String(length=500), nullable=True),
        sa.Column("recorded_by_id", sa.UUID(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["athlete_id"], ["athletes.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["athletic_milestone_id"], ["athletic_milestones.id"]),
        sa.ForeignKeyConstraint(["recorded_by_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_athletic_progress_athlete_id", "athletic_progress", ["athlete_id"])
    op.create_index("ix_athletic_progress_milestone_id", "athletic_progress", ["athletic_milestone_id"])
    op.create_index("ix_athletic_progress_status", "athletic_progress", ["status"])

    # Performance Metrics
    op.create_table(
        "performance_metrics",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("athlete_id", sa.UUID(), nullable=False),
        sa.Column("sport_id", sa.UUID(), nullable=True),
        sa.Column("metric_type", sa.String(length=50), nullable=False),
        sa.Column("value", sa.Float(), nullable=False),
        sa.Column("unit", sa.String(length=30), nullable=False),
        sa.Column("measurement_date", sa.Date(), nullable=False),
        sa.Column("measurement_context", sa.String(length=50), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["athlete_id"], ["athletes.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["sport_id"], ["sports.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_performance_metrics_athlete_id", "performance_metrics", ["athlete_id"])
    op.create_index("ix_performance_metrics_sport_id", "performance_metrics", ["sport_id"])
    op.create_index("ix_performance_metrics_type", "performance_metrics", ["metric_type"])
    op.create_index("ix_performance_metrics_date", "performance_metrics", ["measurement_date"])


def downgrade() -> None:
    # Drop tables in reverse dependency order
    op.drop_index("ix_performance_metrics_date", table_name="performance_metrics")
    op.drop_index("ix_performance_metrics_type", table_name="performance_metrics")
    op.drop_index("ix_performance_metrics_sport_id", table_name="performance_metrics")
    op.drop_index("ix_performance_metrics_athlete_id", table_name="performance_metrics")
    op.drop_table("performance_metrics")

    op.drop_index("ix_athletic_progress_status", table_name="athletic_progress")
    op.drop_index("ix_athletic_progress_milestone_id", table_name="athletic_progress")
    op.drop_index("ix_athletic_progress_athlete_id", table_name="athletic_progress")
    op.drop_table("athletic_progress")

    op.drop_index("ix_recruitment_events_status", table_name="recruitment_events")
    op.drop_index("ix_recruitment_events_event_date", table_name="recruitment_events")
    op.drop_index("ix_recruitment_events_athlete_id", table_name="recruitment_events")
    op.drop_table("recruitment_events")

    op.drop_index("ix_recruitment_contacts_division", table_name="recruitment_contacts")
    op.drop_index("ix_recruitment_contacts_status", table_name="recruitment_contacts")
    op.drop_index("ix_recruitment_contacts_athlete_id", table_name="recruitment_contacts")
    op.drop_table("recruitment_contacts")

    op.drop_index("ix_training_progress_scheduled", table_name="training_progress")
    op.drop_index("ix_training_progress_status", table_name="training_progress")
    op.drop_index("ix_training_progress_session_id", table_name="training_progress")
    op.drop_index("ix_training_progress_athlete_id", table_name="training_progress")
    op.drop_table("training_progress")

    op.drop_index("ix_athlete_training_plans_status", table_name="athlete_training_plans")
    op.drop_index("ix_athlete_training_plans_athlete_id", table_name="athlete_training_plans")
    op.drop_table("athlete_training_plans")

    op.drop_index("ix_training_sessions_week_day", table_name="training_sessions")
    op.drop_index("ix_training_sessions_plan_id", table_name="training_sessions")
    op.drop_table("training_sessions")

    op.drop_index("ix_training_plans_is_template", table_name="training_plans")
    op.drop_index("ix_training_plans_age_stage_id", table_name="training_plans")
    op.drop_index("ix_training_plans_sport_id", table_name="training_plans")
    op.drop_table("training_plans")

    op.drop_index("ix_academic_records_record_type", table_name="academic_records")
    op.drop_index("ix_academic_records_athlete_id", table_name="academic_records")
    op.drop_table("academic_records")

    op.drop_index("ix_athletes_recruitment_status", table_name="athletes")
    op.drop_index("ix_athletes_primary_sport_id", table_name="athletes")
    op.drop_index("ix_athletes_child_id", table_name="athletes")
    op.drop_table("athletes")

    op.drop_index("ix_athletic_milestones_active", table_name="athletic_milestones")
    op.drop_index("ix_athletic_milestones_domain_id", table_name="athletic_milestones")
    op.drop_index("ix_athletic_milestones_age_stage_id", table_name="athletic_milestones")
    op.drop_index("ix_athletic_milestones_sport_id", table_name="athletic_milestones")
    op.drop_table("athletic_milestones")

    op.drop_table("athletic_domains")

    op.drop_index("ix_athletic_age_stages_age_range", table_name="athletic_age_stages")
    op.drop_index("ix_athletic_age_stages_order", table_name="athletic_age_stages")
    op.drop_table("athletic_age_stages")

    op.drop_index("ix_sports_slug", table_name="sports")
    op.drop_table("sports")
