"""
Unit tests for AIAnalyzer
"""

import unittest
from unittest.mock import Mock
from datetime import date
from collections import Counter

from src.services.ai_analyzer import AIAnalyzer


class TestAIAnalyzerInit(unittest.TestCase):
    """Test AIAnalyzer initialization"""

    def test_init_without_client(self):
        """Test initialization without AI client"""
        analyzer = AIAnalyzer()
        self.assertIsNone(analyzer.ai_client)

    def test_init_with_client(self):
        """Test initialization with AI client"""
        mock_client = Mock()
        analyzer = AIAnalyzer(ai_client=mock_client)
        self.assertEqual(analyzer.ai_client, mock_client)


class TestAnalyzeHistoricalPatterns(unittest.TestCase):
    """Test analyze_historical_patterns method"""

    def setUp(self):
        """Set up test fixtures"""
        self.analyzer = AIAnalyzer()

    def test_analyze_patterns_basic(self):
        """Test pattern analysis with basic event data"""
        events = [
            {
                "id": 1,
                "date": "2024-01-01",
                "members": [
                    {"name": "張三", "role": "證道"},
                    {"name": "李四", "role": "司會"}
                ]
            },
            {
                "id": 2,
                "date": "2024-01-08",
                "members": [
                    {"name": "張三", "role": "證道"},
                    {"name": "王五", "role": "司會"}
                ]
            }
        ]

        result = self.analyzer.analyze_historical_patterns(events)

        # Check structure
        self.assertIn("total_events", result)
        self.assertIn("member_frequency", result)
        self.assertIn("role_distribution", result)
        self.assertIn("member_roles", result)
        self.assertIn("workload_balance", result)
        self.assertIn("common_pairings", result)
        self.assertIn("insights", result)

        # Check counts
        self.assertEqual(result["total_events"], 2)
        self.assertEqual(result["member_frequency"]["張三"], 2)
        self.assertEqual(result["member_frequency"]["李四"], 1)
        self.assertEqual(result["member_frequency"]["王五"], 1)

        # Check roles
        self.assertEqual(result["role_distribution"]["證道"], 2)
        self.assertEqual(result["role_distribution"]["司會"], 2)

        # Check member roles
        self.assertIn("證道", result["member_roles"]["張三"])
        self.assertIn("司會", result["member_roles"]["李四"])

    def test_analyze_patterns_empty_events(self):
        """Test pattern analysis with empty event list"""
        events = []

        result = self.analyzer.analyze_historical_patterns(events)

        self.assertEqual(result["total_events"], 0)
        self.assertEqual(result["member_frequency"], {})
        self.assertEqual(result["role_distribution"], {})
        self.assertEqual(result["workload_balance"], {})

    def test_analyze_patterns_workload_balance(self):
        """Test workload balance calculation"""
        events = [
            {"members": [{"name": "張三", "role": "證道"}]},
            {"members": [{"name": "張三", "role": "證道"}]},
            {"members": [{"name": "李四", "role": "司會"}]}
        ]

        result = self.analyzer.analyze_historical_patterns(events)

        # 張三 appeared 2/3 times
        self.assertAlmostEqual(result["workload_balance"]["張三"], 2/3)
        # 李四 appeared 1/3 times
        self.assertAlmostEqual(result["workload_balance"]["李四"], 1/3)

    def test_analyze_patterns_common_pairings(self):
        """Test common pairing detection"""
        events = [
            {"members": [{"name": "張三"}, {"name": "李四"}]},
            {"members": [{"name": "張三"}, {"name": "李四"}]},
            {"members": [{"name": "張三"}, {"name": "王五"}]}
        ]

        result = self.analyzer.analyze_historical_patterns(events)

        # Should have pairings
        self.assertGreater(len(result["common_pairings"]), 0)

        # Most common should be 張三-李四 (2 times)
        top_pairing = result["common_pairings"][0]
        self.assertEqual(top_pairing["count"], 2)
        self.assertIn("張三", top_pairing["members"])
        self.assertIn("李四", top_pairing["members"])


class TestGenerateRoster(unittest.TestCase):
    """Test generate_roster method"""

    def setUp(self):
        """Set up test fixtures"""
        self.analyzer = AIAnalyzer()

    def test_generate_roster_basic(self):
        """Test basic roster generation"""
        target_dates = [date(2024, 1, 15)]
        available_members = {
            "members": {
                "張三": {"available": True},
                "李四": {"available": True}
            }
        }
        historical_patterns = {
            "member_roles": {
                "張三": ["證道"],
                "李四": ["司會"]
            },
            "workload_balance": {
                "張三": 0.5,
                "李四": 0.5
            }
        }
        required_roles = ["證道", "司會"]

        result = self.analyzer.generate_roster(
            target_dates,
            available_members,
            historical_patterns,
            required_roles,
            category="chinese"
        )

        # Check structure
        self.assertEqual(len(result), 1)
        roster = result[0]
        self.assertIn("date", roster)
        self.assertIn("category", roster)
        self.assertIn("assignments", roster)

        # Check assignments
        self.assertEqual(len(roster["assignments"]), 2)
        self.assertEqual(roster["category"], "chinese")

    def test_generate_roster_multiple_dates(self):
        """Test generating roster for multiple dates"""
        target_dates = [
            date(2024, 1, 15),
            date(2024, 1, 22),
            date(2024, 1, 29)
        ]
        available_members = {
            "members": {
                "張三": {"available": True},
                "李四": {"available": True}
            }
        }
        historical_patterns = {
            "member_roles": {},
            "workload_balance": {}
        }
        required_roles = ["證道"]

        result = self.analyzer.generate_roster(
            target_dates,
            available_members,
            historical_patterns,
            required_roles
        )

        self.assertEqual(len(result), 3)
        for roster in result:
            self.assertIn("date", roster)
            self.assertIn("assignments", roster)

    def test_generate_roster_no_available_members(self):
        """Test roster generation with no available members"""
        target_dates = [date(2024, 1, 15)]
        available_members = {"members": {}}
        historical_patterns = {
            "member_roles": {},
            "workload_balance": {}
        }
        required_roles = ["證道"]

        result = self.analyzer.generate_roster(
            target_dates,
            available_members,
            historical_patterns,
            required_roles
        )

        self.assertEqual(len(result), 1)
        # Should still create roster but with empty assignments
        self.assertEqual(len(result[0]["assignments"]), 0)

    def test_generate_roster_workload_distribution(self):
        """Test that roster generation balances workload"""
        target_dates = [date(2024, 1, 15), date(2024, 1, 22)]
        available_members = {
            "members": {
                "張三": {"available": True},
                "李四": {"available": True},
                "王五": {"available": True}
            }
        }
        historical_patterns = {
            "member_roles": {},
            "workload_balance": {
                "張三": 0.8,  # High workload
                "李四": 0.2,  # Low workload
                "王五": 0.1   # Lowest workload
            }
        }
        required_roles = ["證道"]

        result = self.analyzer.generate_roster(
            target_dates,
            available_members,
            historical_patterns,
            required_roles
        )

        # Should prefer members with lower workload
        assigned_members = [
            result[0]["assignments"][0]["name"],
            result[1]["assignments"][0]["name"]
        ]

        # 王五 and 李四 should be preferred over 張三
        self.assertIn("王五", assigned_members)


class TestValidateRoster(unittest.TestCase):
    """Test validate_roster method"""

    def setUp(self):
        """Set up test fixtures"""
        self.analyzer = AIAnalyzer()

    def test_validate_roster_valid_single(self):
        """Test validation of valid single roster"""
        roster = {
            "date": "2024-01-15",
            "assignments": [
                {"role": "證道", "name": "張三"},
                {"role": "司會", "name": "李四"}
            ]
        }

        result = self.analyzer.validate_roster(roster)

        self.assertTrue(result["is_valid"])
        self.assertEqual(len(result["errors"]), 0)
        self.assertEqual(result["statistics"]["total_rosters"], 1)
        self.assertEqual(result["statistics"]["total_assignments"], 2)

    def test_validate_roster_valid_list(self):
        """Test validation of valid roster list"""
        rosters = [
            {
                "date": "2024-01-15",
                "assignments": [{"role": "證道", "name": "張三"}]
            },
            {
                "date": "2024-01-22",
                "assignments": [{"role": "證道", "name": "李四"}]
            }
        ]

        result = self.analyzer.validate_roster(rosters)

        self.assertTrue(result["is_valid"])
        self.assertEqual(result["statistics"]["total_rosters"], 2)
        self.assertEqual(result["statistics"]["total_assignments"], 2)

    def test_validate_roster_duplicate_member(self):
        """Test validation fails for duplicate member assignment"""
        roster = {
            "date": "2024-01-15",
            "assignments": [
                {"role": "證道", "name": "張三"},
                {"role": "司會", "name": "張三"}  # Duplicate
            ]
        }

        result = self.analyzer.validate_roster(roster)

        self.assertFalse(result["is_valid"])
        self.assertGreater(len(result["errors"]), 0)
        self.assertIn("Duplicate", result["errors"][0])

    def test_validate_roster_missing_role(self):
        """Test validation fails for missing role"""
        roster = {
            "date": "2024-01-15",
            "assignments": [
                {"name": "張三"}  # Missing role
            ]
        }

        result = self.analyzer.validate_roster(roster)

        self.assertFalse(result["is_valid"])
        self.assertTrue(any("role" in error for error in result["errors"]))

    def test_validate_roster_missing_name(self):
        """Test validation fails for missing name"""
        roster = {
            "date": "2024-01-15",
            "assignments": [
                {"role": "證道"}  # Missing name
            ]
        }

        result = self.analyzer.validate_roster(roster)

        self.assertFalse(result["is_valid"])
        self.assertTrue(any("name" in error for error in result["errors"]))

    def test_validate_roster_empty_assignments(self):
        """Test validation warning for empty assignments"""
        roster = {
            "date": "2024-01-15",
            "assignments": []
        }

        result = self.analyzer.validate_roster(roster)

        self.assertTrue(result["is_valid"])  # Not an error, just warning
        self.assertGreater(len(result["warnings"]), 0)
        self.assertIn("No assignments", result["warnings"][0])


class TestGenerateInsights(unittest.TestCase):
    """Test _generate_insights method"""

    def setUp(self):
        """Set up test fixtures"""
        self.analyzer = AIAnalyzer()

    def test_generate_insights_basic(self):
        """Test insight generation with basic data"""
        member_frequency = Counter({"張三": 5, "李四": 3, "王五": 2})
        role_distribution = Counter({"證道": 4, "司會": 3, "招待": 3})
        workload_balance = {"張三": 0.5, "李四": 0.3, "王五": 0.2}

        insights = self.analyzer._generate_insights(
            member_frequency,
            role_distribution,
            workload_balance
        )

        self.assertIsInstance(insights, list)
        self.assertGreater(len(insights), 0)

        # Should mention most active members
        self.assertTrue(any("張三" in insight for insight in insights))

    def test_generate_insights_workload_imbalance(self):
        """Test insight generation detects workload imbalance"""
        member_frequency = Counter({"張三": 8, "李四": 2})
        role_distribution = Counter({"證道": 10})
        workload_balance = {"張三": 0.8, "李四": 0.2}

        insights = self.analyzer._generate_insights(
            member_frequency,
            role_distribution,
            workload_balance
        )

        # Should detect imbalance (>30% difference)
        self.assertTrue(any("imbalance" in insight.lower() for insight in insights))


if __name__ == "__main__":
    unittest.main()
