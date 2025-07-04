import base64

import pytest
from pydantic import ValidationError
from user_verification_service.src.domain.schemas.requests import VerificationRequest, VerificationResponse


class TestVerificationResponse:
    """Test cases for VerificationResponse schema."""

    def test_verification_response_creation_with_valid_data(self, valid_verification_response_data):
        # Arrange & Act
        response = VerificationResponse(**valid_verification_response_data)

        # Assert
        assert response.message == valid_verification_response_data["message"]
        assert response.verification_id == valid_verification_response_data["verification_id"]
        assert response.status == valid_verification_response_data["status"]

    def test_verification_response_creation_with_all_string_fields(self):
        # Arrange
        data = {
            "message": "Test message",
            "verification_id": "test-id-123",
            "status": "completed"
        }

        # Act
        response = VerificationResponse(**data)

        # Assert
        assert response.message == "Test message"
        assert response.verification_id == "test-id-123"
        assert response.status == "completed"

    def test_verification_response_with_empty_strings(self):
        # Arrange
        data = {
            "message": "",
            "verification_id": "",
            "status": ""
        }

        # Act
        response = VerificationResponse(**data)

        # Assert
        assert response.message == ""
        assert response.verification_id == ""
        assert response.status == ""

    def test_verification_response_missing_required_fields_raises_error(self):
        # Arrange
        incomplete_data = {"message": "Test"}

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            VerificationResponse(**incomplete_data)

        assert "verification_id" in str(exc_info.value)
        assert "status" in str(exc_info.value)

    def test_verification_response_with_extra_fields_ignored(self):
        # Arrange
        data = {
            "message": "Test message",
            "verification_id": "test-id",
            "status": "pending",
            "extra_field": "should_be_ignored"
        }

        # Act
        response = VerificationResponse(**data)

        # Assert
        assert response.message == "Test message"
        assert response.verification_id == "test-id"
        assert response.status == "pending"
        assert not hasattr(response, "extra_field")


class TestVerificationRequest:
    """Test cases for VerificationRequest schema."""

    def test_verification_request_creation_with_valid_data(self, valid_verification_request_data):
        # Arrange & Act
        request = VerificationRequest(**valid_verification_request_data)

        # Assert
        assert request.user_id == valid_verification_request_data["user_id"]
        assert request.network == valid_verification_request_data["network"]
        assert request.document == valid_verification_request_data["document"]

    def test_verification_request_with_all_supported_networks(self, valid_document_base64):
        # Arrange
        networks = ["ethereum", "tron", "bitcoin"]

        for network in networks:
            data = {
                "user_id": "test_user",
                "network": network,
                "document": valid_document_base64
            }

            # Act
            request = VerificationRequest(**data)

            # Assert
            assert request.network == network.lower()

    def test_verification_request_network_case_insensitive(self, valid_document_base64):
        # Arrange
        test_cases = [
            ("ETHEREUM", "ethereum"),
            ("Ethereum", "ethereum"),
            ("EtHeReUm", "ethereum"),
            ("TRON", "tron"),
            ("Tron", "tron"),
            ("BITCOIN", "bitcoin"),
            ("Bitcoin", "bitcoin")
        ]

        for input_network, expected_network in test_cases:
            data = {
                "user_id": "test_user",
                "network": input_network,
                "document": valid_document_base64
            }

            # Act
            request = VerificationRequest(**data)

            # Assert
            assert request.network == expected_network

    def test_verification_request_with_sample_image(self, sample_image_base64):
        # Arrange
        data = {
            "user_id": "test_user",
            "network": "ethereum",
            "document": sample_image_base64
        }

        # Act
        request = VerificationRequest(**data)

        # Assert
        assert request.document == sample_image_base64
        assert base64.b64decode(request.document)  # Should not raise exception

    def test_verification_request_with_minimal_document(self, minimal_document_base64):
        # Arrange
        data = {
            "user_id": "test_user",
            "network": "ethereum",
            "document": minimal_document_base64
        }

        # Act
        request = VerificationRequest(**data)

        # Assert
        assert request.document == minimal_document_base64

    def test_verification_request_with_large_document(self, large_document_base64):
        # Arrange
        data = {
            "user_id": "test_user",
            "network": "ethereum",
            "document": large_document_base64
        }

        # Act
        request = VerificationRequest(**data)

        # Assert
        assert request.document == large_document_base64

    def test_verification_request_user_id_length_validation(self, valid_document_base64):
        # Arrange
        valid_data = {
            "network": "ethereum",
            "document": valid_document_base64
        }

        # Act & Assert: Test minimum length
        with pytest.raises(ValidationError) as exc_info:
            VerificationRequest(user_id="", **valid_data)
        assert "at least 1 character" in str(exc_info.value)

        # Act & Assert: Test maximum length
        long_user_id = "x" * 256  # Exceeds max_length=255
        with pytest.raises(ValidationError) as exc_info:
            VerificationRequest(user_id=long_user_id, **valid_data)
        assert "at most 255 characters" in str(exc_info.value)

    def test_verification_request_user_id_boundary_values(self, valid_document_base64):
        # Arrange
        base_data = {
            "network": "ethereum",
            "document": valid_document_base64
        }

        # Act & Assert: Test minimum valid length
        request_min = VerificationRequest(user_id="a", **base_data)
        assert request_min.user_id == "a"

        # Act & Assert: Test maximum valid length
        max_user_id = "x" * 255
        request_max = VerificationRequest(user_id=max_user_id, **base_data)
        assert request_max.user_id == max_user_id

    def test_verification_request_network_minimum_length_validation(self, valid_document_base64):
        # Arrange
        data = {
            "user_id": "test_user",
            "network": "",
            "document": valid_document_base64
        }

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            VerificationRequest(**data)
        assert "at least 1 character" in str(exc_info.value)

    def test_verification_request_unsupported_network_raises_error(self, valid_document_base64):
        # Arrange
        unsupported_networks = ["litecoin", "dogecoin", "cardano", "polkadot", "invalid"]

        for network in unsupported_networks:
            data = {
                "user_id": "test_user",
                "network": network,
                "document": valid_document_base64
            }

            # Act & Assert
            with pytest.raises(ValidationError) as exc_info:
                VerificationRequest(**data)
            assert f"Unsupported network: {network}" in str(exc_info.value)

    def test_verification_request_invalid_base64_document_raises_error(self):
        # Arrange
        invalid_base64_strings = [
            "invalid_base64!",
            "not-base64-at-all",
            "123456789",
            "===invalid===",
            "SGVsbG8gV29ybGQ=invalid"
        ]

        for invalid_doc in invalid_base64_strings:
            data = {
                "user_id": "test_user",
                "network": "ethereum",
                "document": invalid_doc
            }

            # Act & Assert
            with pytest.raises(ValidationError) as exc_info:
                VerificationRequest(**data)
            assert "Invalid base64 encoding" in str(exc_info.value)

    def test_verification_request_missing_required_fields_raises_error(self):
        # Arrange
        test_cases = [
            ({}, ["user_id", "network", "document"]),
            ({"user_id": "test"}, ["network", "document"]),
            ({"user_id": "test", "network": "ethereum"}, ["document"]),
            ({"network": "ethereum", "document": "dGVzdA=="}, ["user_id"])
        ]

        for data, expected_missing_fields in test_cases:
            # Act & Assert
            with pytest.raises(ValidationError) as exc_info:
                VerificationRequest(**data)

            error_str = str(exc_info.value)
            for field in expected_missing_fields:
                assert field in error_str

    def test_verification_request_with_special_characters_in_user_id(self, valid_document_base64):
        # Arrange
        special_user_ids = [
            "user@example.com",
            "user-123",
            "user_123",
            "user.123",
            "user+tag",
            "user@domain.com"
        ]

        for user_id in special_user_ids:
            data = {
                "user_id": user_id,
                "network": "ethereum",
                "document": valid_document_base64
            }

            # Act
            request = VerificationRequest(**data)

            # Assert
            assert request.user_id == user_id

    def test_verification_request_document_validator_preserves_valid_base64(self):
        # Arrange
        valid_base64_strings = [
            base64.b64encode(b"hello").decode("utf-8"),
            base64.b64encode(b"test document").decode("utf-8"),
            base64.b64encode(b"").decode("utf-8"),  # Empty content
            "SGVsbG8gV29ybGQ="  # "Hello World" in base64
        ]

        for valid_doc in valid_base64_strings:
            data = {
                "user_id": "test_user",
                "network": "ethereum",
                "document": valid_doc
            }

            # Act
            request = VerificationRequest(**data)

            # Assert
            assert request.document == valid_doc

    def test_verification_request_network_validator_returns_lowercase(self):
        # Arrange
        mixed_case_networks = ["Ethereum", "TRON", "Bitcoin", "ETHEREUM", "tron", "bitcoin"]
        expected_outputs = ["ethereum", "tron", "bitcoin", "ethereum", "tron", "bitcoin"]

        for input_network, expected_output in zip(mixed_case_networks, expected_outputs, strict=False):
            data = {
                "user_id": "test_user",
                "network": input_network,
                "document": base64.b64encode(b"test").decode("utf-8")
            }

            # Act
            request = VerificationRequest(**data)

            # Assert
            assert request.network == expected_output

    def test_verification_request_with_unicode_user_id(self, valid_document_base64):
        # Arrange
        unicode_user_ids = [
            "用户123",
            "пользователь",
            "utilisateur",
            "usuário",
            "ユーザー"
        ]

        for user_id in unicode_user_ids:
            data = {
                "user_id": user_id,
                "network": "ethereum",
                "document": valid_document_base64
            }

            # Act
            request = VerificationRequest(**data)

            # Assert
            assert request.user_id == user_id

    def test_verification_request_json_schema_example_is_valid(self):
        # Arrange
        example_data = {
            "user_id": "user_id",
            "network": "ethereum",
            "document": "iVBORw0KGgoAAAANSUhEUgAAAAUAAAAFCAYAAACNbyblAAAAHElEQVQI12P4//8/w38GIAXDIBKE0DHxgljNBAAO9TXL0Y4OHwAAAABJRU5ErkJggg=="
        }

        # Act
        request = VerificationRequest(**example_data)

        # Assert
        assert request.user_id == "user_id"
        assert request.network == "ethereum"
        assert request.document == example_data["document"]

    def test_verification_request_serialization_to_dict(self, valid_verification_request_data):
        # Arrange
        request = VerificationRequest(**valid_verification_request_data)

        # Act
        request_dict = request.model_dump()

        # Assert
        assert request_dict["user_id"] == valid_verification_request_data["user_id"]
        assert request_dict["network"] == valid_verification_request_data["network"]
        assert request_dict["document"] == valid_verification_request_data["document"]

    def test_verification_request_json_serialization(self, valid_verification_request_data):
        # Arrange
        request = VerificationRequest(**valid_verification_request_data)

        # Act
        json_str = request.model_dump_json()

        # Assert
        assert isinstance(json_str, str)
        assert valid_verification_request_data["user_id"] in json_str
        assert valid_verification_request_data["network"] in json_str
        assert valid_verification_request_data["document"] in json_str
