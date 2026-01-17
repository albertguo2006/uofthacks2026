"""
Configuration for Behavioral Analysis System
Phase 1: Settings and thresholds for suspicious behavior detection
"""

from typing import List, Dict
from models.behavioral_analysis import BehaviorType, SeverityLevel


class BehavioralAnalysisConfig:
    """Configuration for behavioral analysis system"""

    # TwelveLabs Search Queries for Behavior Detection
    BEHAVIOR_QUERIES: List[Dict[str, any]] = [
        # Visual behaviors - HIGH severity
        {
            "behavior_type": BehaviorType.LOOKING_AWAY,
            "query": "person looking away from camera or screen repeatedly",
            "severity": SeverityLevel.HIGH,
            "confidence_threshold": 0.6
        },
        {
            "behavior_type": BehaviorType.MULTIPLE_PEOPLE,
            "query": "multiple people visible in video frame",
            "severity": SeverityLevel.HIGH,
            "confidence_threshold": 0.7
        },
        {
            "behavior_type": BehaviorType.PHONE_USAGE,
            "query": "person using phone or mobile device during interview",
            "severity": SeverityLevel.HIGH,
            "confidence_threshold": 0.7
        },
        {
            "behavior_type": BehaviorType.COVERING_CAMERA,
            "query": "camera being covered or obscured or blocked",
            "severity": SeverityLevel.HIGH,
            "confidence_threshold": 0.8
        },

        # Visual behaviors - MEDIUM severity
        {
            "behavior_type": BehaviorType.READING_EXTERNAL,
            "query": "person reading from paper or another screen or external notes",
            "severity": SeverityLevel.MEDIUM,
            "confidence_threshold": 0.5
        },
        {
            "behavior_type": BehaviorType.ENVIRONMENT_CHANGE,
            "query": "significant background or lighting change in environment",
            "severity": SeverityLevel.MEDIUM,
            "confidence_threshold": 0.6
        },
        {
            "behavior_type": BehaviorType.SCREEN_SHARING_ISSUES,
            "query": "external monitors or additional screens visible in frame",
            "severity": SeverityLevel.MEDIUM,
            "confidence_threshold": 0.5
        },

        # Audio behaviors - HIGH severity
        {
            "behavior_type": BehaviorType.MULTIPLE_VOICES,
            "query": "multiple different voices speaking or conversation with others",
            "severity": SeverityLevel.HIGH,
            "confidence_threshold": 0.7
        },

        # Audio behaviors - MEDIUM severity
        {
            "behavior_type": BehaviorType.WHISPERING,
            "query": "whispering or very quiet speaking or muted conversation",
            "severity": SeverityLevel.MEDIUM,
            "confidence_threshold": 0.6
        },
        {
            "behavior_type": BehaviorType.BACKGROUND_VOICES,
            "query": "other people talking in background or background conversation",
            "severity": SeverityLevel.MEDIUM,
            "confidence_threshold": 0.5
        },

        # Audio behaviors - LOW severity
        {
            "behavior_type": BehaviorType.TYPING_WHILE_SPEAKING,
            "query": "keyboard typing sounds while explaining or during verbal response",
            "severity": SeverityLevel.LOW,
            "confidence_threshold": 0.4
        },

        # Movement behaviors - LOW severity
        {
            "behavior_type": BehaviorType.SUSPICIOUS_MOVEMENT,
            "query": "excessive movement or fidgeting or nervous behavior",
            "severity": SeverityLevel.LOW,
            "confidence_threshold": 0.4
        },
    ]

    # Integrity Score Thresholds
    INTEGRITY_THRESHOLDS = {
        "clean": 0.85,           # Above this = clean session
        "review": 0.70,          # Below this = needs review
        "flag": 0.50,            # Below this = automatic flag
    }

    # Behavior Count Thresholds
    BEHAVIOR_THRESHOLDS = {
        "max_high_severity": 2,      # Max high-severity behaviors before flag
        "max_medium_severity": 4,    # Max medium-severity behaviors before flag
        "max_total_segments": 6,     # Max total suspicious segments before flag
    }

    # Scoring Weights
    SCORING_WEIGHTS = {
        "metrics_weight": 0.70,      # Weight for behavioral metrics in overall score
        "segments_weight": 0.30,     # Weight for suspicious segments in overall score
    }

    # Severity Penalties for Scoring
    SEVERITY_PENALTIES = {
        SeverityLevel.LOW: 0.02,     # Penalty per low-severity segment
        SeverityLevel.MEDIUM: 0.05,  # Penalty per medium-severity segment
        SeverityLevel.HIGH: 0.10,    # Penalty per high-severity segment
    }

    # Metric Impact Weights (how much each behavior affects metrics)
    METRIC_IMPACTS = {
        "eye_contact": {
            BehaviorType.LOOKING_AWAY: 0.3,
            BehaviorType.COVERING_CAMERA: 0.4,
            BehaviorType.READING_EXTERNAL: 0.2,
        },
        "environment": {
            BehaviorType.ENVIRONMENT_CHANGE: 0.3,
            BehaviorType.SCREEN_SHARING_ISSUES: 0.2,
            BehaviorType.MULTIPLE_PEOPLE: 0.4,
        },
        "audio": {
            BehaviorType.MULTIPLE_VOICES: 0.4,
            BehaviorType.WHISPERING: 0.3,
            BehaviorType.BACKGROUND_VOICES: 0.2,
            BehaviorType.TYPING_WHILE_SPEAKING: 0.1,
        },
        "focus": {
            BehaviorType.PHONE_USAGE: 0.4,
            BehaviorType.READING_EXTERNAL: 0.3,
            BehaviorType.MULTIPLE_PEOPLE: 0.3,
            BehaviorType.SUSPICIOUS_MOVEMENT: 0.1,
        },
    }

    # Time-based Settings
    TIME_SETTINGS = {
        "min_segment_duration": 1.0,     # Minimum duration (seconds) for valid segment
        "max_segment_duration": 30.0,    # Maximum duration (seconds) for single segment
        "segment_merge_threshold": 2.0,  # Seconds within which to merge segments
    }

    # Review Priority Calculation
    REVIEW_PRIORITY_RULES = {
        "high": {
            "integrity_score_below": 0.60,
            "high_severity_count_above": 2,
            "flagged_sessions_above": 2,
        },
        "medium": {
            "integrity_score_below": 0.75,
            "high_severity_count_above": 1,
            "flagged_sessions_above": 1,
        },
        "low": {
            "integrity_score_below": 0.85,
            "high_severity_count_above": 0,
            "flagged_sessions_above": 0,
        },
    }

    # Analysis Settings
    ANALYSIS_SETTINGS = {
        "parallel_search": True,          # Run behavior searches in parallel
        "max_search_workers": 5,          # Max concurrent TwelveLabs searches
        "search_timeout": 30,             # Seconds before search timeout
        "cache_results": True,            # Cache analysis results
        "cache_duration": 3600,           # Cache duration in seconds
    }

    # Notification Settings
    NOTIFICATION_SETTINGS = {
        "notify_on_flag": True,           # Notify when session is flagged
        "notify_threshold": 0.70,         # Integrity score threshold for notification
        "batch_notifications": True,      # Batch multiple notifications
        "notification_delay": 300,        # Seconds to wait before sending batch
    }

    @classmethod
    def get_query_for_behavior(cls, behavior_type: BehaviorType) -> Dict:
        """Get search query configuration for a specific behavior type"""
        for query_config in cls.BEHAVIOR_QUERIES:
            if query_config["behavior_type"] == behavior_type:
                return query_config
        return None

    @classmethod
    def get_severity_for_behavior(cls, behavior_type: BehaviorType) -> SeverityLevel:
        """Get severity level for a behavior type"""
        query_config = cls.get_query_for_behavior(behavior_type)
        return query_config["severity"] if query_config else SeverityLevel.LOW

    @classmethod
    def get_confidence_threshold(cls, behavior_type: BehaviorType) -> float:
        """Get confidence threshold for a behavior type"""
        query_config = cls.get_query_for_behavior(behavior_type)
        return query_config["confidence_threshold"] if query_config else 0.5

    @classmethod
    def should_merge_segments(cls, segment1_end: float, segment2_start: float) -> bool:
        """Check if two segments should be merged based on time proximity"""
        gap = segment2_start - segment1_end
        return gap <= cls.TIME_SETTINGS["segment_merge_threshold"]

    @classmethod
    def calculate_review_priority(
        cls,
        integrity_score: float,
        high_severity_count: int,
        flagged_sessions_count: int
    ) -> str:
        """Calculate review priority based on metrics"""
        for priority in ["high", "medium", "low"]:
            rules = cls.REVIEW_PRIORITY_RULES[priority]
            if (integrity_score < rules["integrity_score_below"] or
                high_severity_count > rules["high_severity_count_above"] or
                flagged_sessions_count > rules["flagged_sessions_above"]):
                return priority
        return "low"

    @classmethod
    def get_all_behavior_queries(cls) -> List[str]:
        """Get all TwelveLabs search queries"""
        return [config["query"] for config in cls.BEHAVIOR_QUERIES]

    @classmethod
    def get_high_severity_behaviors(cls) -> List[BehaviorType]:
        """Get list of high severity behavior types"""
        return [
            config["behavior_type"]
            for config in cls.BEHAVIOR_QUERIES
            if config["severity"] == SeverityLevel.HIGH
        ]


# Environment-specific overrides
class DevelopmentConfig(BehavioralAnalysisConfig):
    """Development environment configuration"""
    INTEGRITY_THRESHOLDS = {
        "clean": 0.80,    # More lenient for testing
        "review": 0.60,
        "flag": 0.40,
    }
    ANALYSIS_SETTINGS = {
        **BehavioralAnalysisConfig.ANALYSIS_SETTINGS,
        "cache_results": False,  # Disable caching for development
    }


class ProductionConfig(BehavioralAnalysisConfig):
    """Production environment configuration"""
    ANALYSIS_SETTINGS = {
        **BehavioralAnalysisConfig.ANALYSIS_SETTINGS,
        "max_search_workers": 10,  # More workers in production
        "cache_duration": 7200,     # Longer cache duration
    }


class TestingConfig(BehavioralAnalysisConfig):
    """Testing environment configuration"""
    BEHAVIOR_THRESHOLDS = {
        "max_high_severity": 1,    # More strict for testing
        "max_medium_severity": 2,
        "max_total_segments": 3,
    }
    ANALYSIS_SETTINGS = {
        **BehavioralAnalysisConfig.ANALYSIS_SETTINGS,
        "parallel_search": False,  # Sequential for predictable tests
        "cache_results": False,
    }


# Configuration factory
def get_behavioral_config(environment: str = "development") -> BehavioralAnalysisConfig:
    """Get configuration based on environment"""
    configs = {
        "development": DevelopmentConfig,
        "production": ProductionConfig,
        "testing": TestingConfig,
    }
    return configs.get(environment, DevelopmentConfig)