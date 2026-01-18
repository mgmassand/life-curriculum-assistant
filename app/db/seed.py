"""Database seeding script for curriculum data."""

import asyncio
import json
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import async_session_maker
from app.models.curriculum import Activity, AgeStage, DevelopmentDomain, Milestone
from app.models.resource import Resource
from app.db.seed_athletic import seed_all_athletic

DATA_DIR = Path(__file__).parent.parent.parent / "data"


async def seed_age_stages(db: AsyncSession) -> dict[str, AgeStage]:
    """Seed age stages and return a slug-to-model mapping."""
    # Check if already seeded
    result = await db.execute(select(AgeStage).limit(1))
    if result.scalar_one_or_none():
        print("Age stages already seeded, loading existing...")
        result = await db.execute(select(AgeStage))
        stages = result.scalars().all()
        return {stage.slug: stage for stage in stages}

    print("Seeding age stages...")
    with open(DATA_DIR / "age_stages.json") as f:
        data = json.load(f)

    stages = {}
    for item in data:
        stage = AgeStage(**item)
        db.add(stage)
        stages[item["slug"]] = stage

    await db.flush()
    print(f"  Created {len(stages)} age stages")
    return stages


async def seed_development_domains(db: AsyncSession) -> dict[str, DevelopmentDomain]:
    """Seed development domains and return a slug-to-model mapping."""
    # Check if already seeded
    result = await db.execute(select(DevelopmentDomain).limit(1))
    if result.scalar_one_or_none():
        print("Development domains already seeded, loading existing...")
        result = await db.execute(select(DevelopmentDomain))
        domains = result.scalars().all()
        return {domain.slug: domain for domain in domains}

    print("Seeding development domains...")
    with open(DATA_DIR / "development_domains.json") as f:
        data = json.load(f)

    domains = {}
    for item in data:
        domain = DevelopmentDomain(**item)
        db.add(domain)
        domains[item["slug"]] = domain

    await db.flush()
    print(f"  Created {len(domains)} development domains")
    return domains


async def seed_milestones(
    db: AsyncSession,
    age_stages: dict[str, AgeStage],
    domains: dict[str, DevelopmentDomain],
) -> None:
    """Seed milestones."""
    # Check if already seeded
    result = await db.execute(select(Milestone).limit(1))
    if result.scalar_one_or_none():
        print("Milestones already seeded, skipping...")
        return

    print("Seeding milestones...")
    with open(DATA_DIR / "milestones.json") as f:
        data = json.load(f)

    count = 0
    for item in data:
        age_stage = age_stages.get(item.pop("age_stage_slug"))
        domain = domains.get(item.pop("domain_slug"))

        if not age_stage or not domain:
            print(f"  Skipping milestone: missing age_stage or domain")
            continue

        milestone = Milestone(
            age_stage_id=age_stage.id,
            domain_id=domain.id,
            **item,
        )
        db.add(milestone)
        count += 1

    await db.flush()
    print(f"  Created {count} milestones")


async def seed_activities(
    db: AsyncSession,
    age_stages: dict[str, AgeStage],
    domains: dict[str, DevelopmentDomain],
) -> None:
    """Seed activities."""
    # Check if already seeded
    result = await db.execute(select(Activity).limit(1))
    if result.scalar_one_or_none():
        print("Activities already seeded, skipping...")
        return

    print("Seeding activities...")
    with open(DATA_DIR / "activities.json") as f:
        data = json.load(f)

    count = 0
    for item in data:
        age_stage = age_stages.get(item.pop("age_stage_slug"))
        domain = domains.get(item.pop("domain_slug"))

        if not age_stage or not domain:
            print(f"  Skipping activity: missing age_stage or domain")
            continue

        activity = Activity(
            age_stage_id=age_stage.id,
            domain_id=domain.id,
            **item,
        )
        db.add(activity)
        count += 1

    await db.flush()
    print(f"  Created {count} activities")


async def seed_resources(
    db: AsyncSession,
    age_stages: dict[str, AgeStage],
    domains: dict[str, DevelopmentDomain],
) -> None:
    """Seed resources."""
    # Check if already seeded
    result = await db.execute(select(Resource).limit(1))
    if result.scalar_one_or_none():
        print("Resources already seeded, skipping...")
        return

    print("Seeding resources...")
    with open(DATA_DIR / "resources.json") as f:
        data = json.load(f)

    count = 0
    for item in data:
        # Convert age stage slugs to IDs
        age_stage_slugs = item.pop("age_stages", [])
        age_stage_ids = []
        for slug in age_stage_slugs:
            stage = age_stages.get(slug)
            if stage:
                age_stage_ids.append(str(stage.id))

        # Convert domain slugs to IDs
        domain_slugs = item.pop("domains", [])
        domain_ids = []
        for slug in domain_slugs:
            domain = domains.get(slug)
            if domain:
                domain_ids.append(str(domain.id))

        resource = Resource(
            age_stage_ids=age_stage_ids if age_stage_ids else None,
            domain_ids=domain_ids if domain_ids else None,
            **item,
        )
        db.add(resource)
        count += 1

    await db.flush()
    print(f"  Created {count} resources")


async def seed_all() -> None:
    """Run all seeders."""
    print("\n=== Starting database seeding ===\n")

    async with async_session_maker() as db:
        try:
            # Seed in order (dependencies first)
            age_stages = await seed_age_stages(db)
            domains = await seed_development_domains(db)
            await seed_milestones(db, age_stages, domains)
            await seed_activities(db, age_stages, domains)
            await seed_resources(db, age_stages, domains)

            # Seed Athletic Curriculum data
            await seed_all_athletic(db)

            await db.commit()
            print("\n=== Seeding complete! ===\n")

        except Exception as e:
            await db.rollback()
            print(f"\n=== Seeding failed: {e} ===\n")
            raise


if __name__ == "__main__":
    asyncio.run(seed_all())
