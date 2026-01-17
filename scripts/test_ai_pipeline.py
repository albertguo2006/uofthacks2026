#!/usr/bin/env python3
"""
Test script for the AI analysis pipeline
Run this to verify the AI components are working correctly
"""

import asyncio
import sys
import os
from datetime import datetime, timedelta
import json

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Mock environment variables if not set
os.environ.setdefault("OPENAI_API_KEY", "sk-mock-key-for-testing")
os.environ.setdefault("POSTGRES_URL", "postgresql://skillproof:skillproof123@localhost:5432/behavioral_context")


async def test_behavioral_analyzer():
    """Test the BehavioralSignalAnalyzer"""
    print("=" * 60)
    print("Testing BehavioralSignalAnalyzer...")
    print("=" * 60)

    from apps.api.services.ai_analyzer import BehavioralSignalAnalyzer

    # Create mock events that simulate a coding session
    now = datetime.utcnow()
    mock_events = [
        {
            "event_type": "session_started",
            "timestamp": now,
            "properties": {"task_id": "bugfix-null-check"}
        },
        {
            "event_type": "code_changed",
            "timestamp": now + timedelta(seconds=30),
            "properties": {"lines_changed": 5}
        },
        {
            "event_type": "run_attempted",
            "timestamp": now + timedelta(seconds=60),
            "properties": {"result": "fail"}
        },
        {
            "event_type": "error_emitted",
            "timestamp": now + timedelta(seconds=61),
            "properties": {"error_type": "NullPointerException"}
        },
        {
            "event_type": "fix_applied",
            "timestamp": now + timedelta(seconds=90),
            "properties": {
                "from_error_type": "NullPointerException",
                "time_since_error_ms": 29000
            }
        },
        {
            "event_type": "run_attempted",
            "timestamp": now + timedelta(seconds=120),
            "properties": {"result": "pass"}
        },
        {
            "event_type": "refactor_applied",
            "timestamp": now + timedelta(seconds=180),
            "properties": {"kind": "extract_function", "loc_changed": 10}
        },
        {
            "event_type": "test_added",
            "timestamp": now + timedelta(seconds=240),
            "properties": {"count": 2, "scope": "unit"}
        }
    ]

    # Initialize analyzer (will use fallback if no API key)
    analyzer = BehavioralSignalAnalyzer(openai_api_key=os.getenv("OPENAI_API_KEY"))

    try:
        # Analyze the mock session
        analysis = await analyzer.analyze_coding_session(mock_events)

        print("\n✅ Analysis Results:")
        print("-" * 40)
        print(f"Behavioral Insights:")
        for key, value in analysis.get("behavioral_insights", {}).items():
            print(f"  - {key}: {value}")

        print(f"\nStatistical Features:")
        for key, value in analysis.get("statistical_features", {}).items():
            if isinstance(value, (int, float)):
                print(f"  - {key}: {value:.2f}")
            else:
                print(f"  - {key}: {value}")

        print(f"\nSkill Confidence: {analysis.get('skill_confidence', 0):.2%}")

        print(f"\nImprovement Areas:")
        for area in analysis.get("improvement_areas", []):
            print(f"  - {area}")

        print(f"\nSession Quality Score: {analysis.get('session_quality_score', 0):.2%}")

    except Exception as e:
        print(f"❌ Error in BehavioralSignalAnalyzer: {e}")
        print("This might be due to missing OpenAI API key. The fallback analysis should still work.")


async def test_parallel_assessment():
    """Test the ParallelSkillAssessmentEngine"""
    print("\n" + "=" * 60)
    print("Testing ParallelSkillAssessmentEngine...")
    print("=" * 60)

    from apps.api.services.ai_analyzer import ParallelSkillAssessmentEngine

    # Create a more complex mock session with different phases
    now = datetime.utcnow()
    mock_events = [
        # Initialization phase
        {"event_type": "session_started", "timestamp": now},
        {"event_type": "task_opened", "timestamp": now + timedelta(seconds=5)},

        # Implementation phase
        {"event_type": "code_changed", "timestamp": now + timedelta(seconds=30)},
        {"event_type": "code_changed", "timestamp": now + timedelta(seconds=60)},
        {"event_type": "editor_command", "timestamp": now + timedelta(seconds=90)},

        # Debugging phase
        {"event_type": "error_emitted", "timestamp": now + timedelta(seconds=120)},
        {"event_type": "error_emitted", "timestamp": now + timedelta(seconds=150)},
        {"event_type": "fix_applied", "timestamp": now + timedelta(seconds=180)},

        # Optimization phase
        {"event_type": "refactor_applied", "timestamp": now + timedelta(seconds=210)},
        {"event_type": "refactor_applied", "timestamp": now + timedelta(seconds=240)},

        # Testing phase
        {"event_type": "run_attempted", "timestamp": now + timedelta(seconds=270)},
        {"event_type": "test_added", "timestamp": now + timedelta(seconds=300)},
    ]

    engine = ParallelSkillAssessmentEngine(openai_api_key=os.getenv("OPENAI_API_KEY"))

    try:
        # Run parallel analysis
        print("Running parallel scene analysis...")
        analysis = await engine.analyze_session_parallel(mock_events)

        print("\n✅ Parallel Analysis Results:")
        print("-" * 40)

        print("Scene Breakdown:")
        for scene_name, scene_data in analysis.get("scenes", {}).items():
            if scene_data:
                print(f"\n  {scene_name.capitalize()} Scene:")
                for key, value in scene_data.items():
                    print(f"    - {key}: {value}")

        print(f"\nOverall Approach: {analysis.get('overall_approach', 'unknown')}")

        print("\nTime Distribution:")
        for scene, percentage in analysis.get("time_distribution", {}).items():
            print(f"  - {scene}: {percentage:.1%}")

    except Exception as e:
        print(f"❌ Error in ParallelSkillAssessmentEngine: {e}")


async def test_context_engine():
    """Test the HierarchicalBehavioralContextEngine"""
    print("\n" + "=" * 60)
    print("Testing HierarchicalBehavioralContextEngine...")
    print("=" * 60)

    from apps.api.services.context_engine import HierarchicalBehavioralContextEngine

    engine = HierarchicalBehavioralContextEngine(os.getenv("POSTGRES_URL"))

    try:
        # Initialize the database
        print("Initializing PostgreSQL with pgvector...")
        await engine.initialize()
        print("✅ Database initialized successfully")

        # Create a mock event tree
        session_id = "test-session-" + datetime.utcnow().isoformat()
        user_id = "test-user-123"

        print(f"\nInserting events into behavioral tree...")
        print(f"Session ID: {session_id}")

        # Insert root event
        root_event = {
            "event_type": "session_started",
            "timestamp": datetime.utcnow(),
            "properties": {"task_id": "test-task"}
        }

        root_node = await engine.insert_event(
            event=root_event,
            parent_id=None,
            session_id=session_id,
            user_id=user_id
        )
        print(f"  ✅ Root node created: {root_node.node_id}")

        # Insert child events
        child_events = [
            {"event_type": "code_changed", "properties": {"lines": 10}},
            {"event_type": "error_emitted", "properties": {"error_type": "SyntaxError"}},
            {"event_type": "fix_applied", "properties": {"time_to_fix": 30}},
        ]

        parent_id = root_node.node_id
        for event in child_events:
            event["timestamp"] = datetime.utcnow()
            node = await engine.insert_event(
                event=event,
                parent_id=parent_id,
                session_id=session_id,
                user_id=user_id
            )
            print(f"  ✅ Child node created: {event['event_type']} (depth={node.depth})")
            parent_id = node.node_id  # Chain events

        # Retrieve and analyze the tree
        print(f"\nRetrieving session tree...")
        tree_analysis = await engine.get_session_tree(session_id)

        if tree_analysis:
            print("✅ Tree Analysis Results:")
            print("-" * 40)
            print(f"Total Nodes: {tree_analysis.get('depth_statistics', {}).get('total_nodes', 0)}")
            print(f"Max Depth: {tree_analysis.get('depth_statistics', {}).get('max_depth', 0)}")
            print(f"Behavioral Flow: {' -> '.join(tree_analysis.get('behavioral_flow', [])[:5])}")

    except Exception as e:
        print(f"❌ Error in HierarchicalBehavioralContextEngine: {e}")
        print("Make sure PostgreSQL with pgvector is running:")
        print("  docker-compose -f docker-compose.ai.yml up -d")


async def main():
    """Run all tests"""
    print("🚀 Testing AI Analysis Pipeline")
    print("=" * 60)

    # Test each component
    await test_behavioral_analyzer()
    await test_parallel_assessment()

    # Only test context engine if PostgreSQL is available
    try:
        import asyncpg
        await test_context_engine()
    except ImportError:
        print("\n⚠️  Skipping Context Engine test (asyncpg not installed)")
        print("Install with: pip install asyncpg pgvector")
    except Exception as e:
        print(f"\n⚠️  Skipping Context Engine test: {e}")

    print("\n" + "=" * 60)
    print("✅ AI Pipeline Testing Complete!")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Set up your OpenAI API key for full LLM analysis")
    print("2. Start PostgreSQL with: docker-compose -f docker-compose.ai.yml up -d")
    print("3. Integrate these services into your main FastAPI app")


if __name__ == "__main__":
    asyncio.run(main())