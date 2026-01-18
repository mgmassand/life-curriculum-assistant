"""Script to update resource URLs in the database."""

import asyncio
import json
from pathlib import Path

from sqlalchemy import select, delete
from app.db.session import async_session_maker
from app.models.resource import Resource
from app.models.curriculum import AgeStage, DevelopmentDomain

DATA_DIR = Path(__file__).parent / "data"


async def update_resources():
    """Delete existing resources and re-seed with updated URLs."""
    print("\n=== Updating Resources with Real URLs ===\n")

    async with async_session_maker() as db:
        try:
            # Load age stages and domains for reference
            result = await db.execute(select(AgeStage))
            age_stages = {stage.slug: stage for stage in result.scalars().all()}

            result = await db.execute(select(DevelopmentDomain))
            domains = {domain.slug: domain for domain in result.scalars().all()}

            # Delete existing resources
            await db.execute(delete(Resource))
            print("Deleted existing resources")

            # Load new resources from JSON
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

            await db.commit()
            print(f"Created {count} resources with real URLs")
            print("\n=== Update complete! ===\n")

        except Exception as e:
            await db.rollback()
            print(f"\n=== Update failed: {e} ===\n")
            raise


if __name__ == "__main__":
    asyncio.run(update_resources())
