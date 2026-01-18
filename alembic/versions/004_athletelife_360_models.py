"""Add AthleteLife 360 models.

Revision ID: 004
Revises: 003
Create Date: 2026-01-13 17:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "004"
down_revision: Union[str, None] = "003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Athlete Physiology - Growth Spurt Guardian (PHV tracking)
    op.create_table(
        "athlete_physiology",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("athlete_id", sa.UUID(), nullable=False),
        sa.Column("measurement_date", sa.Date(), nullable=False),
        sa.Column("height_cm", sa.Float(), nullable=False),
        sa.Column("weight_kg", sa.Float(), nullable=True),
        sa.Column("sitting_height_cm", sa.Float(), nullable=True),
        sa.Column("leg_length_cm", sa.Float(), nullable=True),
        sa.Column("arm_span_cm", sa.Float(), nullable=True),
        sa.Column("maturity_offset", sa.Float(), nullable=True),
        sa.Column("phv_status", sa.String(length=30), nullable=True),
        sa.Column("estimated_phv_date", sa.Date(), nullable=True),
        sa.Column("growth_velocity_cm_month", sa.Float(), nullable=True),
        sa.Column("recommended_modifications", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("injury_risk_factors", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["athlete_id"], ["athletes.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_athlete_physiology_athlete_id", "athlete_physiology", ["athlete_id"])
    op.create_index("ix_athlete_physiology_date", "athlete_physiology", ["measurement_date"])

    # Activity Logs - Play-o-Meter
    op.create_table(
        "activity_logs",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("athlete_id", sa.UUID(), nullable=False),
        sa.Column("activity_date", sa.Date(), nullable=False),
        sa.Column("activity_type", sa.String(length=30), nullable=False),
        sa.Column("sport_id", sa.UUID(), nullable=True),
        sa.Column("duration_minutes", sa.Integer(), nullable=False),
        sa.Column("intensity", sa.String(length=20), nullable=False, server_default="moderate"),
        sa.Column("context", sa.String(length=50), nullable=True),
        sa.Column("location", sa.String(length=100), nullable=True),
        sa.Column("training_load", sa.Float(), nullable=True),
        sa.Column("rpe", sa.Integer(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("logged_by_id", sa.UUID(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["athlete_id"], ["athletes.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["sport_id"], ["sports.id"]),
        sa.ForeignKeyConstraint(["logged_by_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_activity_logs_athlete_id", "activity_logs", ["athlete_id"])
    op.create_index("ix_activity_logs_date", "activity_logs", ["activity_date"])
    op.create_index("ix_activity_logs_type", "activity_logs", ["activity_type"])

    # Fun Check-ins - Emoji enjoyment tracking
    op.create_table(
        "fun_check_ins",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("athlete_id", sa.UUID(), nullable=False),
        sa.Column("check_in_date", sa.Date(), nullable=False),
        sa.Column("activity_log_id", sa.UUID(), nullable=True),
        sa.Column("fun_rating", sa.Integer(), nullable=False),
        sa.Column("energy_rating", sa.Integer(), nullable=True),
        sa.Column("friend_rating", sa.Integer(), nullable=True),
        sa.Column("favorite_moment", sa.String(length=500), nullable=True),
        sa.Column("want_to_do_again", sa.Boolean(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["athlete_id"], ["athletes.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["activity_log_id"], ["activity_logs.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint("fun_rating >= 1 AND fun_rating <= 5", name="fun_rating_range"),
        sa.CheckConstraint("energy_rating IS NULL OR (energy_rating >= 1 AND energy_rating <= 5)", name="energy_rating_range"),
        sa.CheckConstraint("friend_rating IS NULL OR (friend_rating >= 1 AND friend_rating <= 5)", name="friend_rating_range"),
    )
    op.create_index("ix_fun_check_ins_athlete_id", "fun_check_ins", ["athlete_id"])
    op.create_index("ix_fun_check_ins_date", "fun_check_ins", ["check_in_date"])

    # Parent Learning Modules - Parent University
    op.create_table(
        "parent_learning_modules",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("slug", sa.String(length=100), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("content_type", sa.String(length=30), nullable=False),
        sa.Column("duration_seconds", sa.Integer(), nullable=False, server_default="60"),
        sa.Column("video_url", sa.String(length=500), nullable=True),
        sa.Column("content_html", sa.Text(), nullable=True),
        sa.Column("category", sa.String(length=50), nullable=False),
        sa.Column("age_stage_id", sa.UUID(), nullable=True),
        sa.Column("sport_id", sa.UUID(), nullable=True),
        sa.Column("tags", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("source", sa.String(length=255), nullable=True),
        sa.Column("author", sa.String(length=255), nullable=True),
        sa.Column("expert_verified", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["age_stage_id"], ["athletic_age_stages.id"]),
        sa.ForeignKeyConstraint(["sport_id"], ["sports.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug"),
    )
    op.create_index("ix_parent_learning_modules_slug", "parent_learning_modules", ["slug"])
    op.create_index("ix_parent_learning_modules_category", "parent_learning_modules", ["category"])

    # User Learning Progress
    op.create_table(
        "user_learning_progress",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("module_id", sa.UUID(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="not_started"),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("progress_percent", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("quiz_score", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["module_id"], ["parent_learning_modules.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_user_learning_progress_user_id", "user_learning_progress", ["user_id"])
    op.create_index("ix_user_learning_progress_module_id", "user_learning_progress", ["module_id"])

    # Motor Skill Assessments - Sport Sampler AI
    op.create_table(
        "motor_skill_assessments",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("athlete_id", sa.UUID(), nullable=False),
        sa.Column("assessment_date", sa.Date(), nullable=False),
        sa.Column("locomotor_score", sa.Integer(), nullable=True),
        sa.Column("stability_score", sa.Integer(), nullable=True),
        sa.Column("object_control_score", sa.Integer(), nullable=True),
        sa.Column("spatial_awareness_score", sa.Integer(), nullable=True),
        sa.Column("speed_score", sa.Integer(), nullable=True),
        sa.Column("endurance_score", sa.Integer(), nullable=True),
        sa.Column("flexibility_score", sa.Integer(), nullable=True),
        sa.Column("power_score", sa.Integer(), nullable=True),
        sa.Column("recommended_sports", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("strengths", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("areas_to_develop", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("overall_physical_literacy_score", sa.Integer(), nullable=True),
        sa.Column("assessed_by", sa.String(length=100), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["athlete_id"], ["athletes.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_motor_skill_assessments_athlete_id", "motor_skill_assessments", ["athlete_id"])
    op.create_index("ix_motor_skill_assessments_date", "motor_skill_assessments", ["assessment_date"])

    # Calendar Events - Academic-Athletic Load Balancer
    op.create_table(
        "calendar_events",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("athlete_id", sa.UUID(), nullable=False),
        sa.Column("event_type", sa.String(length=30), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("start_datetime", sa.DateTime(), nullable=False),
        sa.Column("end_datetime", sa.DateTime(), nullable=True),
        sa.Column("all_day", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("location", sa.String(length=255), nullable=True),
        sa.Column("priority", sa.String(length=20), nullable=False, server_default="normal"),
        sa.Column("stress_factor", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("is_mandatory", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("sport_id", sa.UUID(), nullable=True),
        sa.Column("academic_subject", sa.String(length=100), nullable=True),
        sa.Column("is_recurring", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("recurrence_rule", sa.String(length=255), nullable=True),
        sa.Column("parent_event_id", sa.UUID(), nullable=True),
        sa.Column("color", sa.String(length=20), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["athlete_id"], ["athletes.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["sport_id"], ["sports.id"]),
        sa.ForeignKeyConstraint(["parent_event_id"], ["calendar_events.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_calendar_events_athlete_id", "calendar_events", ["athlete_id"])
    op.create_index("ix_calendar_events_start_datetime", "calendar_events", ["start_datetime"])
    op.create_index("ix_calendar_events_type", "calendar_events", ["event_type"])

    # Injury Risk Logs - ACWR Dashboard
    op.create_table(
        "injury_risk_logs",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("athlete_id", sa.UUID(), nullable=False),
        sa.Column("calculation_date", sa.Date(), nullable=False),
        sa.Column("acute_load", sa.Float(), nullable=False),
        sa.Column("chronic_load", sa.Float(), nullable=False),
        sa.Column("acwr", sa.Float(), nullable=False),
        sa.Column("risk_level", sa.String(length=20), nullable=False),
        sa.Column("risk_score", sa.Integer(), nullable=False),
        sa.Column("weekly_hours", sa.Float(), nullable=True),
        sa.Column("weekly_sessions", sa.Integer(), nullable=True),
        sa.Column("rest_days", sa.Integer(), nullable=True),
        sa.Column("high_intensity_sessions", sa.Integer(), nullable=True),
        sa.Column("phv_adjustment", sa.Float(), nullable=True),
        sa.Column("growth_spurt_flag", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("recommendations", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("alerts", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["athlete_id"], ["athletes.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_injury_risk_logs_athlete_id", "injury_risk_logs", ["athlete_id"])
    op.create_index("ix_injury_risk_logs_date", "injury_risk_logs", ["calculation_date"])
    op.create_index("ix_injury_risk_logs_risk_level", "injury_risk_logs", ["risk_level"])

    # Conversation Scripts - Car Ride Home Coach
    op.create_table(
        "conversation_scripts",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("slug", sa.String(length=100), nullable=False),
        sa.Column("context_type", sa.String(length=50), nullable=False),
        sa.Column("outcome_type", sa.String(length=30), nullable=True),
        sa.Column("emotion_type", sa.String(length=30), nullable=True),
        sa.Column("age_stage_id", sa.UUID(), nullable=True),
        sa.Column("sport_id", sa.UUID(), nullable=True),
        sa.Column("opening_prompt", sa.Text(), nullable=False),
        sa.Column("talking_points", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("questions_to_ask", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("phrases_to_avoid", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("closing_suggestion", sa.Text(), nullable=True),
        sa.Column("source", sa.String(length=255), nullable=True),
        sa.Column("expert_verified", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["age_stage_id"], ["athletic_age_stages.id"]),
        sa.ForeignKeyConstraint(["sport_id"], ["sports.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug"),
    )
    op.create_index("ix_conversation_scripts_slug", "conversation_scripts", ["slug"])
    op.create_index("ix_conversation_scripts_context_type", "conversation_scripts", ["context_type"])

    # NCAA Courses - Eligibility Tracker
    op.create_table(
        "ncaa_courses",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("athlete_id", sa.UUID(), nullable=False),
        sa.Column("course_name", sa.String(length=255), nullable=False),
        sa.Column("course_code", sa.String(length=50), nullable=True),
        sa.Column("subject_area", sa.String(length=50), nullable=False),
        sa.Column("grade_level", sa.Integer(), nullable=False),
        sa.Column("semester", sa.String(length=20), nullable=False),
        sa.Column("school_year", sa.String(length=20), nullable=False),
        sa.Column("credits", sa.Float(), nullable=False),
        sa.Column("grade", sa.String(length=5), nullable=True),
        sa.Column("grade_points", sa.Float(), nullable=True),
        sa.Column("is_ncaa_approved", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("ncaa_course_code", sa.String(length=50), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="planned"),
        sa.Column("is_core_course", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["athlete_id"], ["athletes.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_ncaa_courses_athlete_id", "ncaa_courses", ["athlete_id"])
    op.create_index("ix_ncaa_courses_subject_area", "ncaa_courses", ["subject_area"])
    op.create_index("ix_ncaa_courses_grade_level", "ncaa_courses", ["grade_level"])

    # Financial Projections - ROI Calculator
    op.create_table(
        "financial_projections",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("athlete_id", sa.UUID(), nullable=False),
        sa.Column("projection_date", sa.Date(), nullable=False),
        sa.Column("projection_type", sa.String(length=30), nullable=False),
        sa.Column("annual_travel_team_cost", sa.Float(), nullable=True),
        sa.Column("annual_training_cost", sa.Float(), nullable=True),
        sa.Column("annual_equipment_cost", sa.Float(), nullable=True),
        sa.Column("annual_travel_cost", sa.Float(), nullable=True),
        sa.Column("annual_tournament_cost", sa.Float(), nullable=True),
        sa.Column("total_annual_investment", sa.Float(), nullable=True),
        sa.Column("cumulative_investment", sa.Float(), nullable=True),
        sa.Column("target_school", sa.String(length=255), nullable=True),
        sa.Column("target_division", sa.String(length=20), nullable=True),
        sa.Column("annual_cost_of_attendance", sa.Float(), nullable=True),
        sa.Column("projected_scholarship_percent", sa.Float(), nullable=True),
        sa.Column("projected_annual_aid", sa.Float(), nullable=True),
        sa.Column("net_annual_cost", sa.Float(), nullable=True),
        sa.Column("four_year_total_cost", sa.Float(), nullable=True),
        sa.Column("scholarship_probability", sa.Float(), nullable=True),
        sa.Column("expected_value", sa.Float(), nullable=True),
        sa.Column("roi_ratio", sa.Float(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("assumptions", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["athlete_id"], ["athletes.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_financial_projections_athlete_id", "financial_projections", ["athlete_id"])
    op.create_index("ix_financial_projections_date", "financial_projections", ["projection_date"])

    # NIL Deals - NIL Education Suite
    op.create_table(
        "nil_deals",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("athlete_id", sa.UUID(), nullable=False),
        sa.Column("brand_name", sa.String(length=255), nullable=False),
        sa.Column("deal_type", sa.String(length=50), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="potential"),
        sa.Column("start_date", sa.Date(), nullable=True),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column("total_value", sa.Float(), nullable=True),
        sa.Column("payment_structure", sa.String(length=50), nullable=True),
        sa.Column("in_kind_value", sa.Float(), nullable=True),
        sa.Column("deliverables", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("exclusivity_terms", sa.Text(), nullable=True),
        sa.Column("disclosed_to_school", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("school_approval_date", sa.Date(), nullable=True),
        sa.Column("compliant_with_state_law", sa.Boolean(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["athlete_id"], ["athletes.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_nil_deals_athlete_id", "nil_deals", ["athlete_id"])
    op.create_index("ix_nil_deals_status", "nil_deals", ["status"])

    # Knowledge Documents - AthleTEQ AI RAG
    op.create_table(
        "knowledge_documents",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("source", sa.String(length=255), nullable=False),
        sa.Column("source_url", sa.String(length=1000), nullable=True),
        sa.Column("document_type", sa.String(length=50), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("category", sa.String(length=50), nullable=False),
        sa.Column("sport_id", sa.UUID(), nullable=True),
        sa.Column("age_stage_id", sa.UUID(), nullable=True),
        sa.Column("tags", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("embedding_id", sa.String(length=255), nullable=True),
        sa.Column("chunk_index", sa.Integer(), nullable=True),
        sa.Column("publication_date", sa.Date(), nullable=True),
        sa.Column("last_verified", sa.Date(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["sport_id"], ["sports.id"]),
        sa.ForeignKeyConstraint(["age_stage_id"], ["athletic_age_stages.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_knowledge_documents_category", "knowledge_documents", ["category"])
    op.create_index("ix_knowledge_documents_source", "knowledge_documents", ["source"])
    op.create_index("ix_knowledge_documents_sport_id", "knowledge_documents", ["sport_id"])


def downgrade() -> None:
    op.drop_table("knowledge_documents")
    op.drop_table("nil_deals")
    op.drop_table("financial_projections")
    op.drop_table("ncaa_courses")
    op.drop_table("conversation_scripts")
    op.drop_table("injury_risk_logs")
    op.drop_table("calendar_events")
    op.drop_table("motor_skill_assessments")
    op.drop_table("user_learning_progress")
    op.drop_table("parent_learning_modules")
    op.drop_table("fun_check_ins")
    op.drop_table("activity_logs")
    op.drop_table("athlete_physiology")
