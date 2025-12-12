"""Unit tests for agile/scrum validation."""

from specfact_cli.validators.agile_validation import AgileValidator


class TestAgileValidator:
    """Test suite for AgileValidator."""

    def test_validate_dor_complete(self) -> None:
        """Test DoR validation with complete story."""
        validator = AgileValidator()
        story = {
            "key": "STORY-001",
            "story_points": 5,
            "value_points": 8,
            "priority": "P1",
            "business_value_description": "Improves user experience",
            "depends_on_stories": [],
            "blocks_stories": [],
            "due_date": "2025-12-31",
        }
        errors = validator.validate_dor(story)
        assert len(errors) == 0

    def test_validate_dor_missing_story_points(self) -> None:
        """Test DoR validation with missing story points."""
        validator = AgileValidator()
        story = {
            "key": "STORY-001",
            "value_points": 8,
            "priority": "P1",
            "business_value_description": "Improves user experience",
        }
        errors = validator.validate_dor(story)
        assert len(errors) > 0
        assert any("Missing story points" in e for e in errors)

    def test_validate_dor_missing_value_points(self) -> None:
        """Test DoR validation with missing value points."""
        validator = AgileValidator()
        story = {
            "key": "STORY-001",
            "story_points": 5,
            "priority": "P1",
            "business_value_description": "Improves user experience",
        }
        errors = validator.validate_dor(story)
        assert len(errors) > 0
        assert any("Missing value points" in e for e in errors)

    def test_validate_dor_missing_priority(self) -> None:
        """Test DoR validation with missing priority."""
        validator = AgileValidator()
        story = {
            "key": "STORY-001",
            "story_points": 5,
            "value_points": 8,
            "business_value_description": "Improves user experience",
        }
        errors = validator.validate_dor(story)
        assert len(errors) > 0
        assert any("Missing priority" in e for e in errors)

    def test_validate_dor_missing_business_value(self) -> None:
        """Test DoR validation with missing business value."""
        validator = AgileValidator()
        story = {
            "key": "STORY-001",
            "story_points": 5,
            "value_points": 8,
            "priority": "P1",
        }
        errors = validator.validate_dor(story)
        assert len(errors) > 0
        assert any("Missing business value description" in e for e in errors)

    def test_validate_dor_invalid_story_points(self) -> None:
        """Test DoR validation with invalid story points."""
        validator = AgileValidator()
        story = {
            "key": "STORY-001",
            "story_points": 99,  # Invalid
            "value_points": 8,
            "priority": "P1",
            "business_value_description": "Improves user experience",
        }
        errors = validator.validate_dor(story)
        assert len(errors) > 0
        assert any("Invalid story points" in e for e in errors)

    def test_validate_dor_invalid_priority(self) -> None:
        """Test DoR validation with invalid priority."""
        validator = AgileValidator()
        story = {
            "key": "STORY-001",
            "story_points": 5,
            "value_points": 8,
            "priority": "P5",  # Invalid
            "business_value_description": "Improves user experience",
        }
        errors = validator.validate_dor(story)
        assert len(errors) > 0
        assert any("Invalid priority" in e for e in errors)

    def test_validate_dor_invalid_date_format(self) -> None:
        """Test DoR validation with invalid date format."""
        validator = AgileValidator()
        story = {
            "key": "STORY-001",
            "story_points": 5,
            "value_points": 8,
            "priority": "P1",
            "business_value_description": "Improves user experience",
            "due_date": "2025/01/15",  # Invalid format
        }
        errors = validator.validate_dor(story)
        assert len(errors) > 0
        assert any("Invalid date format" in e for e in errors)

    def test_validate_dependency_integrity_valid(self) -> None:
        """Test dependency integrity validation with valid dependencies."""
        validator = AgileValidator()
        stories = [
            {"key": "STORY-001", "depends_on_stories": [], "blocks_stories": []},
            {"key": "STORY-002", "depends_on_stories": ["STORY-001"], "blocks_stories": []},
        ]
        features = {}
        errors = validator.validate_dependency_integrity(stories, features)
        assert len(errors) == 0

    def test_validate_dependency_integrity_missing_reference(self) -> None:
        """Test dependency integrity validation with missing reference."""
        validator = AgileValidator()
        stories = [
            {"key": "STORY-001", "depends_on_stories": ["STORY-999"], "blocks_stories": []},
        ]
        features = {}
        errors = validator.validate_dependency_integrity(stories, features)
        assert len(errors) > 0
        assert any("does not exist" in e for e in errors)

    def test_validate_dependency_integrity_circular(self) -> None:
        """Test dependency integrity validation with circular dependency."""
        validator = AgileValidator()
        stories = [
            {"key": "STORY-001", "depends_on_stories": ["STORY-002"], "blocks_stories": []},
            {"key": "STORY-002", "depends_on_stories": ["STORY-001"], "blocks_stories": []},
        ]
        features = {}
        errors = validator.validate_dependency_integrity(stories, features)
        assert len(errors) > 0
        assert any("Circular dependency" in e for e in errors)

    def test_validate_feature_prioritization_valid(self) -> None:
        """Test feature prioritization validation with valid data."""
        validator = AgileValidator()
        feature = {
            "key": "FEATURE-001",
            "priority": "P1",
            "business_value_score": 75,
            "business_value_description": "Improves user experience",
        }
        errors = validator.validate_feature_prioritization(feature)
        assert len(errors) == 0

    def test_validate_feature_prioritization_invalid_score(self) -> None:
        """Test feature prioritization validation with invalid business value score."""
        validator = AgileValidator()
        feature = {
            "key": "FEATURE-001",
            "priority": "P1",
            "business_value_score": 150,  # Invalid (>100)
        }
        errors = validator.validate_feature_prioritization(feature)
        assert len(errors) > 0
        assert any("Invalid business value score" in e for e in errors)

    def test_validate_story_point_ranges_valid(self) -> None:
        """Test story point range validation with valid values."""
        validator = AgileValidator()
        stories = [
            {"key": "STORY-001", "story_points": 5, "value_points": 8},
            {"key": "STORY-002", "story_points": 13, "value_points": 21},
        ]
        errors = validator.validate_story_point_ranges(stories)
        assert len(errors) == 0

    def test_validate_story_point_ranges_invalid(self) -> None:
        """Test story point range validation with invalid values."""
        validator = AgileValidator()
        stories = [
            {"key": "STORY-001", "story_points": 99, "value_points": 8},
        ]
        errors = validator.validate_story_point_ranges(stories)
        assert len(errors) > 0
        assert any("not in valid range" in e for e in errors)

    def test_validate_date_format_valid(self) -> None:
        """Test date format validation with valid ISO 8601 date."""
        validator = AgileValidator()
        assert validator.validate_date_format("2025-01-15") is True

    def test_validate_date_format_invalid(self) -> None:
        """Test date format validation with invalid date."""
        validator = AgileValidator()
        assert validator.validate_date_format("2025/01/15") is False
        assert validator.validate_date_format("01-15-2025") is False

    def test_validate_bundle_agile_requirements_complete(self) -> None:
        """Test full bundle validation with complete agile requirements."""
        validator = AgileValidator()
        bundle_data = {
            "features": {
                "FEATURE-001": {
                    "key": "FEATURE-001",
                    "priority": "P1",
                    "business_value_score": 75,
                    "business_value_description": "Improves user experience",
                    "stories": [
                        {
                            "key": "STORY-001",
                            "story_points": 5,
                            "value_points": 8,
                            "priority": "P1",
                            "business_value_description": "Enables secure login",
                            "depends_on_stories": [],
                            "blocks_stories": [],
                        }
                    ],
                }
            }
        }
        errors = validator.validate_bundle_agile_requirements(bundle_data)
        assert len(errors) == 0

    def test_validate_bundle_agile_requirements_incomplete(self) -> None:
        """Test full bundle validation with incomplete agile requirements."""
        validator = AgileValidator()
        bundle_data = {
            "features": {
                "FEATURE-001": {
                    "key": "FEATURE-001",
                    "stories": [
                        {
                            "key": "STORY-001",
                            # Missing required DoR fields
                        }
                    ],
                }
            }
        }
        errors = validator.validate_bundle_agile_requirements(bundle_data)
        assert len(errors) > 0
        assert any("Missing story points" in e for e in errors)
        assert any("Missing value points" in e for e in errors)
        assert any("Missing priority" in e for e in errors)
        assert any("Missing business value description" in e for e in errors)
