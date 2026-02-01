#!/usr/bin/env python3
"""Seed the database with initial Nigerian celebrities."""

import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.models import Celebrity


# Nigerian celebrities to seed
SEED_CELEBRITIES = [
    {
        "instagram_username": "davido",
        "full_name": "David Adeleke (Davido)",
        "category": "musician",
        "follower_count": 28000000,
        "scrape_priority": 10,
    },
    {
        "instagram_username": "burabornaboy",
        "full_name": "Damini Ogulu (Burna Boy)",
        "category": "musician",
        "follower_count": 12000000,
        "scrape_priority": 10,
    },
    {
        "instagram_username": "wizkidayo",
        "full_name": "Ayodeji Balogun (Wizkid)",
        "category": "musician",
        "follower_count": 16000000,
        "scrape_priority": 10,
    },
    {
        "instagram_username": "taboriajayi",
        "full_name": "Tiwa Savage",
        "category": "musician",
        "follower_count": 14000000,
        "scrape_priority": 9,
    },
    {
        "instagram_username": "funaborkeakindele",
        "full_name": "Funke Akindele-Bello",
        "category": "actor",
        "follower_count": 18000000,
        "scrape_priority": 8,
    },
    {
        "instagram_username": "aboromajoyadekunle",
        "full_name": "Toyin Abraham",
        "category": "actor",
        "follower_count": 13000000,
        "scrape_priority": 8,
    },
    {
        "instagram_username": "mercyaborjohnson",
        "full_name": "Mercy Johnson Okojie",
        "category": "actor",
        "follower_count": 12000000,
        "scrape_priority": 8,
    },
    {
        "instagram_username": "symaborply",
        "full_name": "Iyabo Ojo",
        "category": "actor",
        "follower_count": 9000000,
        "scrape_priority": 7,
    },
    {
        "instagram_username": "don_jazzy",
        "full_name": "Michael Collins Ajereh (Don Jazzy)",
        "category": "musician",
        "follower_count": 14000000,
        "scrape_priority": 9,
    },
    {
        "instagram_username": "theaborreal_tboss",
        "full_name": "Tokunbo Idowu (TBoss)",
        "category": "influencer",
        "follower_count": 5000000,
        "scrape_priority": 6,
    },
    {
        "instagram_username": "ayaborcomedian",
        "full_name": "Ayo Makun (AY)",
        "category": "comedian",
        "follower_count": 8000000,
        "scrape_priority": 7,
    },
    {
        "instagram_username": "aborboratalkwithbasket",
        "full_name": "Basketmouth",
        "category": "comedian",
        "follower_count": 6000000,
        "scrape_priority": 7,
    },
]


async def seed_celebrities():
    """Seed celebrities into the database."""
    async with AsyncSessionLocal() as session:
        added = 0
        skipped = 0

        for celeb_data in SEED_CELEBRITIES:
            # Check if already exists
            result = await session.execute(
                select(Celebrity).where(
                    Celebrity.instagram_username == celeb_data["instagram_username"]
                )
            )
            existing = result.scalar_one_or_none()

            if existing:
                print(f"Skipping @{celeb_data['instagram_username']} (already exists)")
                skipped += 1
                continue

            celebrity = Celebrity(**celeb_data)
            session.add(celebrity)
            print(f"Added @{celeb_data['instagram_username']}")
            added += 1

        await session.commit()

        print(f"\nSeeding complete: {added} added, {skipped} skipped")


if __name__ == "__main__":
    print("Seeding Nigerian celebrities...")
    asyncio.run(seed_celebrities())
