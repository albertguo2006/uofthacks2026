"""
MongoDB Schema Migration for Behavioral Analysis
Phase 1: Add behavioral analysis fields to videos and passports collections
"""

import asyncio
from datetime import datetime
from typing import Optional
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from apps.api.db.collections import Collections
from apps.api.db.mongo import init_db
from apps.api.models.behavioral_analysis import (
    BehavioralMetrics,
    ProctoringMetrics,
    BehavioralPattern,
    ReviewStatus
)


async def migrate_videos_collection():
    """
    Add behavioral_analysis field to existing video documents
    """
    print("Starting videos collection migration...")

    videos_collection = Collections.videos()

    # Count existing documents
    total_count = await videos_collection.count_documents({})
    print(f"Found {total_count} video documents to migrate")

    # Add behavioral_analysis field to documents that don't have it
    update_result = await videos_collection.update_many(
        {"behavioral_analysis": {"$exists": False}},
        {
            "$set": {
                "behavioral_analysis": None  # Will be populated when analysis runs
            }
        }
    )

    print(f"Updated {update_result.modified_count} video documents with behavioral_analysis field")

    # Create indexes for efficient querying
    await videos_collection.create_index("behavioral_analysis.overall_integrity_score")
    await videos_collection.create_index("behavioral_analysis.flagged_for_review")
    await videos_collection.create_index([
        ("user_id", 1),
        ("behavioral_analysis.analyzed_at", -1)
    ])

    print("Created indexes for behavioral analysis queries")


async def migrate_passports_collection():
    """
    Add proctoring_metrics field to existing passport documents
    """
    print("\nStarting passports collection migration...")

    passports_collection = Collections.passports()

    # Count existing documents
    total_count = await passports_collection.count_documents({})
    print(f"Found {total_count} passport documents to migrate")

    # Default proctoring metrics for existing passports
    default_proctoring_metrics = {
        "overall_integrity_score": 1.0,
        "total_sessions_analyzed": 0,
        "flagged_sessions_count": 0,
        "behavioral_patterns": {
            "consistent_environment": True,
            "maintains_focus": True,
            "professional_conduct": True
        },
        "common_flags": [],
        "review_status": "clean",
        "reviewer_notes": None,
        "last_reviewed_at": None,
        "reviewed_by": None
    }

    # Add proctoring_metrics field to documents that don't have it
    update_result = await passports_collection.update_many(
        {"proctoring_metrics": {"$exists": False}},
        {
            "$set": {
                "proctoring_metrics": default_proctoring_metrics
            }
        }
    )

    print(f"Updated {update_result.modified_count} passport documents with proctoring_metrics field")

    # Create indexes for efficient querying
    await passports_collection.create_index("proctoring_metrics.overall_integrity_score")
    await passports_collection.create_index("proctoring_metrics.review_status")
    await passports_collection.create_index("proctoring_metrics.flagged_sessions_count")

    print("Created indexes for proctoring metrics queries")


async def migrate_proctoring_sessions_collection():
    """
    Add behavioral analysis fields to proctoring sessions
    """
    print("\nStarting proctoring_sessions collection migration...")

    proctoring_collection = Collections.proctoring_sessions()

    # Count existing documents
    total_count = await proctoring_collection.count_documents({})
    print(f"Found {total_count} proctoring session documents to migrate")

    # Add new fields for behavioral analysis
    update_result = await proctoring_collection.update_many(
        {
            "$or": [
                {"video_analyzed": {"$exists": False}},
                {"integrity_score": {"$exists": False}},
                {"behavioral_analysis_id": {"$exists": False}}
            ]
        },
        {
            "$set": {
                "video_analyzed": False,
                "integrity_score": None,
                "flagged_for_review": False,
                "behavioral_analysis_id": None
            }
        }
    )

    print(f"Updated {update_result.modified_count} proctoring session documents")

    # Create indexes
    await proctoring_collection.create_index("integrity_score")
    await proctoring_collection.create_index("flagged_for_review")
    await proctoring_collection.create_index([
        ("user_id", 1),
        ("video_analyzed", 1)
    ])

    print("Created indexes for proctoring session queries")


async def create_behavioral_analytics_collection():
    """
    Create a new collection for storing behavioral analytics summaries
    """
    print("\nCreating behavioral_analytics collection...")

    db = Collections.db()

    # Check if collection exists
    existing_collections = await db.list_collection_names()

    if "behavioral_analytics" not in existing_collections:
        # Create the collection
        await db.create_collection("behavioral_analytics")
        print("Created behavioral_analytics collection")

        # Create indexes
        analytics_collection = db.behavioral_analytics
        await analytics_collection.create_index("user_id", unique=True)
        await analytics_collection.create_index("average_integrity_score")
        await analytics_collection.create_index("requires_manual_review")
        await analytics_collection.create_index("review_priority")

        print("Created indexes for behavioral_analytics collection")
    else:
        print("behavioral_analytics collection already exists")


async def verify_migration():
    """
    Verify that migration was successful
    """
    print("\nVerifying migration...")

    # Check videos collection
    videos_collection = Collections.videos()
    sample_video = await videos_collection.find_one({})
    if sample_video:
        has_behavioral = "behavioral_analysis" in sample_video
        print(f"✓ Videos collection: behavioral_analysis field exists = {has_behavioral}")

    # Check passports collection
    passports_collection = Collections.passports()
    sample_passport = await passports_collection.find_one({})
    if sample_passport:
        has_proctoring = "proctoring_metrics" in sample_passport
        print(f"✓ Passports collection: proctoring_metrics field exists = {has_proctoring}")

    # Check proctoring_sessions collection
    proctoring_collection = Collections.proctoring_sessions()
    sample_session = await proctoring_collection.find_one({})
    if sample_session:
        has_video_analyzed = "video_analyzed" in sample_session
        has_integrity = "integrity_score" in sample_session
        print(f"✓ Proctoring sessions: video_analyzed field exists = {has_video_analyzed}")
        print(f"✓ Proctoring sessions: integrity_score field exists = {has_integrity}")

    # Check behavioral_analytics collection exists
    db = Collections.db()
    collections = await db.list_collection_names()
    has_analytics = "behavioral_analytics" in collections
    print(f"✓ Behavioral analytics collection exists = {has_analytics}")

    print("\nMigration verification complete!")


async def rollback_migration():
    """
    Rollback migration by removing added fields (use with caution)
    """
    print("\n⚠️  Starting rollback of behavioral analysis migration...")

    response = input("Are you sure you want to rollback? This will remove all behavioral analysis data. (yes/no): ")
    if response.lower() != "yes":
        print("Rollback cancelled")
        return

    # Remove fields from videos collection
    videos_collection = Collections.videos()
    result = await videos_collection.update_many(
        {},
        {"$unset": {"behavioral_analysis": ""}}
    )
    print(f"Removed behavioral_analysis from {result.modified_count} video documents")

    # Remove fields from passports collection
    passports_collection = Collections.passports()
    result = await passports_collection.update_many(
        {},
        {"$unset": {"proctoring_metrics": ""}}
    )
    print(f"Removed proctoring_metrics from {result.modified_count} passport documents")

    # Remove fields from proctoring_sessions collection
    proctoring_collection = Collections.proctoring_sessions()
    result = await proctoring_collection.update_many(
        {},
        {"$unset": {
            "video_analyzed": "",
            "integrity_score": "",
            "flagged_for_review": "",
            "behavioral_analysis_id": ""
        }}
    )
    print(f"Updated {result.modified_count} proctoring session documents")

    # Drop behavioral_analytics collection
    db = Collections.db()
    await db.behavioral_analytics.drop()
    print("Dropped behavioral_analytics collection")

    print("\nRollback complete!")


async def main():
    """
    Main migration function
    """
    print("=" * 60)
    print("MongoDB Schema Migration for Behavioral Analysis")
    print("Phase 1: Data Schema Extensions")
    print("=" * 60)

    # Initialize database connection
    await init_db()

    # Check for command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] == "--rollback":
            await rollback_migration()
            return
        elif sys.argv[1] == "--verify":
            await verify_migration()
            return

    # Run migrations
    try:
        await migrate_videos_collection()
        await migrate_passports_collection()
        await migrate_proctoring_sessions_collection()
        await create_behavioral_analytics_collection()
        await verify_migration()

        print("\n✅ Migration completed successfully!")
        print("\nNext steps:")
        print("1. Update API endpoints to use new models")
        print("2. Implement TwelveLabs behavioral analysis service")
        print("3. Test with sample videos")

    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        print("Run with --rollback flag to undo changes")
        raise


if __name__ == "__main__":
    asyncio.run(main())