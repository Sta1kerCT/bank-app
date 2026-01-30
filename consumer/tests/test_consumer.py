"""
Tests for Kafka consumer
"""
import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
import json
from datetime import datetime
import sys
import os

# Добавляем пути для импорта
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'server'))
from app.models.database import Account, Transaction

# Импортируем функции для тестирования
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from app.consumer import process_transaction, get_db_session


class TestConsumer:
    """Test cases for Kafka consumer"""

    @pytest.fixture
    def sample_transaction_data(self):
        """Sample transaction data from Kafka"""
        return {
            "transaction_id": 1,
            "from_account": "ACC001",
            "to_account": "ACC002",
            "amount": 100.0,
            "transaction_type": "TRANSFER",
            "created_at": "2023-01-01T00:00:00"
        }

    @pytest.fixture
    def mock_db_session(self):
        """Mock database session"""
        session = AsyncMock()

        # Mock account queries
        from_account = Mock(spec=Account)
        from_account.account_number = "ACC001"
        from_account.balance = 500.0
        from_account.is_active = True

        to_account = Mock(spec=Account)
        to_account.account_number = "ACC002"
        to_account.balance = 300.0
        to_account.is_active = True

        # Mock session.execute results
        session.execute.return_value.scalar_one_or_none.side_effect = [
            from_account,  # First call returns from_account
            to_account  # Second call returns to_account
        ]

        # Mock scalar() for transaction query
        transaction = Mock(spec=Transaction)
        transaction.id = 1
        session.execute.return_value.scalar.return_value = transaction

        return session

    @pytest.mark.asyncio
    async def test_process_deposit_transaction(self, sample_transaction_data, mock_db_session):
        """Test processing DEPOSIT transaction"""
        # Modify data for deposit
        deposit_data = sample_transaction_data.copy()
        deposit_data["transaction_type"] = "DEPOSIT"
        deposit_data["from_account"] = None

        with patch('consumer.app.consumer.get_db_session') as mock_get_session:
            mock_get_session.return_value.__aenter__.return_value = mock_db_session

            await process_transaction(deposit_data)

            # Verify transaction was updated
            mock_db_session.execute.assert_called()
            mock_db_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_withdraw_transaction(self, sample_transaction_data, mock_db_session):
        """Test processing WITHDRAW transaction"""
        withdraw_data = sample_transaction_data.copy()
        withdraw_data["transaction_type"] = "WITHDRAW"
        withdraw_data["to_account"] = "ACC001"  # Same as from_account for withdrawal

        with patch('consumer.app.consumer.get_db_session') as mock_get_session:
            mock_get_session.return_value.__aenter__.return_value = mock_db_session

            await process_transaction(withdraw_data)

            # Verify update was called for account balance
            assert mock_db_session.execute.call_count >= 2

    @pytest.mark.asyncio
    async def test_process_transfer_transaction(self, sample_transaction_data, mock_db_session):
        """Test processing TRANSFER transaction"""
        with patch('consumer.app.consumer.get_db_session') as mock_get_session:
            mock_get_session.return_value.__aenter__.return_value = mock_db_session

            await process_transaction(sample_transaction_data)

            # Should update both accounts
            assert mock_db_session.execute.call_count >= 3

    @pytest.mark.asyncio
    async def test_process_transaction_insufficient_funds(self, sample_transaction_data, mock_db_session):
        """Test transaction with insufficient funds"""
        # Make from_account have insufficient balance
        from_account = Mock(spec=Account)
        from_account.account_number = "ACC001"
        from_account.balance = 50.0  # Less than transaction amount
        from_account.is_active = True

        to_account = Mock(spec=Account)
        to_account.account_number = "ACC002"
        to_account.balance = 300.0
        to_account.is_active = True

        mock_db_session.execute.return_value.scalar_one_or_none.side_effect = [
            from_account, to_account
        ]

        with patch('consumer.app.consumer.get_db_session') as mock_get_session:
            mock_get_session.return_value.__aenter__.return_value = mock_db_session

            await process_transaction(sample_transaction_data)

            # Should rollback on error
            mock_db_session.rollback.assert_called_once()
            mock_db_session.commit.assert_not_called()

    @pytest.mark.asyncio
    async def test_process_transaction_account_not_found(self, sample_transaction_data, mock_db_session):
        """Test transaction with non-existent account"""
        # Return None for account (not found)
        mock_db_session.execute.return_value.scalar_one_or_none.return_value = None

        with patch('consumer.app.consumer.get_db_session') as mock_get_session:
            mock_get_session.return_value.__aenter__.return_value = mock_db_session

            await process_transaction(sample_transaction_data)

            # Should rollback
            mock_db_session.rollback.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_transaction_inactive_account(self, sample_transaction_data, mock_db_session):
        """Test transaction with inactive account"""
        from_account = Mock(spec=Account)
        from_account.account_number = "ACC001"
        from_account.balance = 500.0
        from_account.is_active = False  # Inactive account

        mock_db_session.execute.return_value.scalar_one_or_none.return_value = from_account

        with patch('consumer.app.consumer.get_db_session') as mock_get_session:
            mock_get_session.return_value.__aenter__.return_value = mock_db_session

            await process_transaction(sample_transaction_data)

            # Should rollback
            mock_db_session.rollback.assert_called_once()

    def test_consume_transactions_mock_kafka(self):
        """Test Kafka consumer with mocked Kafka"""
        mock_message = Mock()
        mock_message.value = {
            "transaction_id": 1,
            "from_account": "ACC001",
            "to_account": "ACC002",
            "amount": 100.0,
            "transaction_type": "TRANSFER",
            "created_at": "2023-01-01T00:00:00"
        }

        mock_consumer = Mock()
        mock_consumer.__iter__.return_value = [mock_message]

        with patch('consumer.app.consumer.KafkaConsumer') as mock_kafka:
            mock_kafka.return_value = mock_consumer
            with patch('consumer.app.consumer.asyncio.run') as mock_asyncio:
                # Mock the process_transaction function
                with patch('consumer.app.consumer.process_transaction') as mock_process:
                    # Импортируем и запускаем
                    from consumer.app.consumer import consume_transactions

                    # Запускаем consumer (он остановится после одного сообщения)
                    try:
                        consume_transactions()
                    except StopIteration:
                        pass  # Ожидаемо, так как мы мокаем итератор

                    # Проверяем что процесс был вызван
                    mock_process.assert_called_once_with(mock_message.value)

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_integration_transaction_flow(self):
        """Integration test: create transaction via API and process via consumer"""
        # This would be a more complex integration test
        # that requires running services
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])