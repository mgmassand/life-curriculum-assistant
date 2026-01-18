"""Athletic curriculum seeding functions."""

import json
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.athletic import (
    Sport,
    AthleticAgeStage,
    AthleticDomain,
    AthleticMilestone,
    TrainingPlan,
)

DATA_DIR = Path(__file__).parent.parent.parent / "data"


async def seed_sports(db: AsyncSession) -> dict[str, Sport]:
    """Seed sports and return a slug-to-model mapping."""
    result = await db.execute(select(Sport).limit(1))
    if result.scalar_one_or_none():
        print("Sports already seeded, loading existing...")
        result = await db.execute(select(Sport))
        sports = result.scalars().all()
        return {sport.slug: sport for sport in sports}

    print("Seeding sports...")
    with open(DATA_DIR / "sports.json") as f:
        data = json.load(f)

    sports = {}
    for item in data:
        sport = Sport(**item)
        db.add(sport)
        sports[item["slug"]] = sport

    await db.flush()
    print(f"  Created {len(sports)} sports")
    return sports


async def seed_athletic_age_stages(db: AsyncSession) -> dict[str, AthleticAgeStage]:
    """Seed athletic age stages and return a slug-to-model mapping."""
    result = await db.execute(select(AthleticAgeStage).limit(1))
    if result.scalar_one_or_none():
        print("Athletic age stages already seeded, loading existing...")
        result = await db.execute(select(AthleticAgeStage))
        stages = result.scalars().all()
        return {stage.slug: stage for stage in stages}

    print("Seeding athletic age stages...")
    with open(DATA_DIR / "athletic_age_stages.json") as f:
        data = json.load(f)

    stages = {}
    for item in data:
        stage = AthleticAgeStage(**item)
        db.add(stage)
        stages[item["slug"]] = stage

    await db.flush()
    print(f"  Created {len(stages)} athletic age stages")
    return stages


async def seed_athletic_domains(db: AsyncSession) -> dict[str, AthleticDomain]:
    """Seed athletic domains and return a slug-to-model mapping."""
    result = await db.execute(select(AthleticDomain).limit(1))
    if result.scalar_one_or_none():
        print("Athletic domains already seeded, loading existing...")
        result = await db.execute(select(AthleticDomain))
        domains = result.scalars().all()
        return {domain.slug: domain for domain in domains}

    print("Seeding athletic domains...")
    with open(DATA_DIR / "athletic_domains.json") as f:
        data = json.load(f)

    domains = {}
    for item in data:
        domain = AthleticDomain(**item)
        db.add(domain)
        domains[item["slug"]] = domain

    await db.flush()
    print(f"  Created {len(domains)} athletic domains")
    return domains


async def seed_athletic_milestones(
    db: AsyncSession,
    sports: dict[str, Sport],
    athletic_age_stages: dict[str, AthleticAgeStage],
    athletic_domains: dict[str, AthleticDomain],
) -> None:
    """Seed athletic milestones."""
    result = await db.execute(select(AthleticMilestone).limit(1))
    if result.scalar_one_or_none():
        print("Athletic milestones already seeded, skipping...")
        return

    print("Seeding athletic milestones...")
    with open(DATA_DIR / "athletic_milestones.json") as f:
        data = json.load(f)

    count = 0
    for item in data:
        sport_slug = item.pop("sport_slug", None)
        age_stage_slug = item.pop("athletic_age_stage_slug")
        domain_slug = item.pop("domain_slug")

        sport = sports.get(sport_slug) if sport_slug else None
        age_stage = athletic_age_stages.get(age_stage_slug)
        domain = athletic_domains.get(domain_slug)

        if not age_stage or not domain:
            print(f"  Skipping milestone: missing age_stage or domain")
            continue

        milestone = AthleticMilestone(
            sport_id=sport.id if sport else None,
            athletic_age_stage_id=age_stage.id,
            athletic_domain_id=domain.id,
            **item,
        )
        db.add(milestone)
        count += 1

    await db.flush()
    print(f"  Created {count} athletic milestones")


async def seed_training_plans(
    db: AsyncSession,
    sports: dict[str, Sport],
    athletic_age_stages: dict[str, AthleticAgeStage],
) -> None:
    """Seed training plan templates."""
    result = await db.execute(select(TrainingPlan).limit(1))
    if result.scalar_one_or_none():
        print("Training plans already seeded, skipping...")
        return

    print("Seeding training plans...")
    with open(DATA_DIR / "training_templates.json") as f:
        data = json.load(f)

    count = 0
    for item in data:
        sport_slug = item.pop("sport_slug", None)
        age_stage_slug = item.pop("athletic_age_stage_slug")

        sport = sports.get(sport_slug) if sport_slug else None
        age_stage = athletic_age_stages.get(age_stage_slug)

        if not age_stage:
            print(f"  Skipping training plan: missing age_stage")
            continue

        plan = TrainingPlan(
            sport_id=sport.id if sport else None,
            athletic_age_stage_id=age_stage.id,
            **item,
        )
        db.add(plan)
        count += 1

    await db.flush()
    print(f"  Created {count} training plans")


async def seed_all_athletic(db: AsyncSession) -> None:
    """Run all athletic seeders."""
    print("\n--- Seeding Athletic Curriculum data ---\n")
    sports = await seed_sports(db)
    athletic_age_stages = await seed_athletic_age_stages(db)
    athletic_domains = await seed_athletic_domains(db)
    await seed_athletic_milestones(db, sports, athletic_age_stages, athletic_domains)
    await seed_training_plans(db, sports, athletic_age_stages)
