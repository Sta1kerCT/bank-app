import pytest
from unittest.mock import Mock, patch
from app import BankClient


def test_create_account_success():
    with patch('requests.Session.post') as mock_post:
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.json.return_value = {
            "account_number": "TEST123",
            "owner_name": "Test User",
            "balance": 1000.0
        }
        mock_post.return_value = mock_response

        client = BankClient("http://test-server")
        result = client.create_account("Test User", 1000)

        assert result is not None
        assert result["account_number"] == "TEST123"
        assert result["owner_name"] == "Test User"


def test_deposit_success():
    with patch('requests.Session.post') as mock_post:
        mock_response = Mock()
        mock_response.status_code = 202
        mock_response.json.return_value = {
            "id": 1,
            "status": "PENDING",
            "amount": 500.0
        }
        mock_post.return_value = mock_response

        client = BankClient("http://test-server")
        result = client.deposit("TEST123", 500)

        assert result is not None
        assert result["id"] == 1
        assert result["status"] == "PENDING"


def test_get_account_not_found():
    with patch('requests.Session.get') as mock_get:
        mock_response = Mock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response

        client = BankClient("http://test-server")
        result = client.get_account("NONEXISTENT")

        assert result is None


def test_health_check_success():
    with patch('requests.Session.get') as mock_get:
        mock_response = Mock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        client = BankClient("http://test-server")
        result = client.health_check()

        assert result is True