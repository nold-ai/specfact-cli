"""Unit tests for OpenAPI contract models."""

from specfact_cli.models.contract import ContractMetadata, ContractStatus, count_endpoints, validate_openapi_schema


class TestContractMetadata:
    """Test suite for ContractMetadata model."""

    def test_default_openapi_version(self) -> None:
        """Test default OpenAPI version is 3.0.3."""
        from datetime import UTC, datetime

        contract = ContractMetadata(
            feature_key="FEATURE-001",
            contract_file="contracts/FEATURE-001.openapi.yaml",
            openapi_version="3.0.3",
            created_at=datetime.now(UTC).isoformat(),
            updated_at=datetime.now(UTC).isoformat(),
            status=ContractStatus.DRAFT,
            validated_at=None,
            tested_at=None,
            coverage=0.0,
        )
        assert contract.openapi_version == "3.0.3"

    def test_contract_metadata_creation(self) -> None:
        """Test creating contract metadata."""
        from datetime import UTC, datetime

        contract = ContractMetadata(
            feature_key="FEATURE-001",
            contract_file="contracts/FEATURE-001.openapi.yaml",
            status=ContractStatus.VALIDATED,
            openapi_version="3.0.3",
            created_at=datetime.now(UTC).isoformat(),
            updated_at=datetime.now(UTC).isoformat(),
            validated_at=None,
            tested_at=None,
            coverage=0.0,
        )

        assert contract.feature_key == "FEATURE-001"
        assert contract.contract_file == "contracts/FEATURE-001.openapi.yaml"
        assert contract.status == ContractStatus.VALIDATED
        assert contract.openapi_version == "3.0.3"


class TestValidateOpenAPISchema:
    """Test suite for validate_openapi_schema function."""

    def test_validate_valid_openapi_3_0(self) -> None:
        """Test validation of valid OpenAPI 3.0 schema."""
        contract_data = {
            "openapi": "3.0.3",
            "info": {"title": "Test API", "version": "1.0.0"},
            "paths": {
                "/users": {
                    "get": {
                        "responses": {
                            "200": {
                                "description": "Success",
                            }
                        }
                    }
                }
            },
        }

        assert validate_openapi_schema(contract_data) is True

    def test_validate_valid_openapi_3_1(self) -> None:
        """Test validation of valid OpenAPI 3.1 schema (forward-compatible)."""
        contract_data = {
            "openapi": "3.1.0",
            "info": {"title": "Test API", "version": "1.0.0"},
            "paths": {
                "/users": {
                    "get": {
                        "responses": {
                            "200": {
                                "description": "Success",
                            }
                        }
                    }
                }
            },
        }

        assert validate_openapi_schema(contract_data) is True

    def test_validate_missing_openapi_field(self) -> None:
        """Test validation fails when openapi field is missing."""
        contract_data = {
            "info": {"title": "Test API", "version": "1.0.0"},
            "paths": {},
        }

        assert validate_openapi_schema(contract_data) is False

    def test_validate_missing_info_field(self) -> None:
        """Test validation fails when info field is missing."""
        contract_data = {
            "openapi": "3.0.3",
            "paths": {},
        }

        assert validate_openapi_schema(contract_data) is False

    def test_validate_missing_paths_field(self) -> None:
        """Test validation fails when paths field is missing."""
        contract_data = {
            "openapi": "3.0.3",
            "info": {"title": "Test API", "version": "1.0.0"},
        }

        assert validate_openapi_schema(contract_data) is False

    def test_validate_invalid_version(self) -> None:
        """Test validation fails for invalid OpenAPI version."""
        contract_data = {
            "openapi": "2.0",
            "info": {"title": "Test API", "version": "1.0.0"},
            "paths": {},
        }

        assert validate_openapi_schema(contract_data) is False


class TestCountEndpoints:
    """Test suite for count_endpoints function."""

    def test_count_endpoints_single_path(self) -> None:
        """Test counting endpoints in a single path."""
        contract_data = {
            "openapi": "3.0.3",
            "info": {"title": "Test API", "version": "1.0.0"},
            "paths": {
                "/users": {
                    "get": {"responses": {"200": {"description": "Success"}}},
                    "post": {"responses": {"201": {"description": "Created"}}},
                }
            },
        }

        assert count_endpoints(contract_data) == 2

    def test_count_endpoints_multiple_paths(self) -> None:
        """Test counting endpoints across multiple paths."""
        contract_data = {
            "openapi": "3.0.3",
            "info": {"title": "Test API", "version": "1.0.0"},
            "paths": {
                "/users": {
                    "get": {"responses": {"200": {"description": "Success"}}},
                    "post": {"responses": {"201": {"description": "Created"}}},
                },
                "/posts": {
                    "get": {"responses": {"200": {"description": "Success"}}},
                    "put": {"responses": {"200": {"description": "Updated"}}},
                    "delete": {"responses": {"204": {"description": "Deleted"}}},
                },
            },
        }

        assert count_endpoints(contract_data) == 5

    def test_count_endpoints_no_paths(self) -> None:
        """Test counting endpoints when no paths exist."""
        contract_data = {
            "openapi": "3.0.3",
            "info": {"title": "Test API", "version": "1.0.0"},
            "paths": {},
        }

        assert count_endpoints(contract_data) == 0

    def test_count_endpoints_with_parameters(self) -> None:
        """Test counting endpoints with path parameters."""
        contract_data = {
            "openapi": "3.0.3",
            "info": {"title": "Test API", "version": "1.0.0"},
            "paths": {
                "/users/{id}": {
                    "get": {"responses": {"200": {"description": "Success"}}},
                    "put": {"responses": {"200": {"description": "Updated"}}},
                }
            },
        }

        assert count_endpoints(contract_data) == 2
