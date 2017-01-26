"""
tests/test_base_page_handler.py

Test the base page handler and the convenience methods I've added.
"""

import pytest
import asyncio

from unittest.mock import MagicMock

from src.routes._base import BasePageHandler


class TestBasePageHandler(object):
    """Base page handler"""

    def test_data_received_not_implemented(self):
        """Should return nothing when streaming response. (Not implemented, overwrite later)"""
        base_page_handler = BasePageHandler(MagicMock(), MagicMock())
        assert base_page_handler.data_received(None) is None
        assert base_page_handler.data_received('some data') is None

    def test_property_db_gets_application_db(self):
        """Should give the application db property on its db property."""
        app_stub = MagicMock()
        base_page_handler = BasePageHandler(app_stub, MagicMock())
        db = base_page_handler.db
        assert db is app_stub.db

    def test_property_scheduler_gets_application_scheduler(self):
        """Should give the application scheduler property on its scheduler property."""
        app_stub = MagicMock()
        base_page_handler = BasePageHandler(app_stub, MagicMock())
        scheduler = base_page_handler.scheduler
        assert scheduler is app_stub.scheduler

    @pytest.mark.asyncio
    async def test_get_db_cursor_on_get_cursor(self):
        """Should get a database cursor on get_cursor."""

        # Create a stubbed version of the tornado app
        app_stub = MagicMock()

        # Create a stubbed future for the result of application.db.cursor()
        cursor_future = asyncio.Future()
        cursor_future.set_result('result_of_future')

        # Add the future to the stub
        app_stub.db.cursor.return_value = cursor_future

        # Create the base page handler
        base_page_handler = BasePageHandler(app_stub, MagicMock())

        # Call the bit of code we are testing
        cursor = await base_page_handler.get_cursor()

        # Assert the retrieved cursor is result of stubbed future
        assert cursor is 'result_of_future'
        app_stub.db.cursor.assert_called_once()

    @pytest.mark.asyncio
    async def test_proxy_validate_auth_token_on_validate_auth_token(self):
        """Should proxy call to validate auth token to application validator."""

        # Create a stubbed version of the tornado app
        app_stub = MagicMock()

        # Create a stubbed future for the result of application.validate_auth_token()
        validator_future = asyncio.Future()
        validator_future.set_result('result_of_future')

        # Add the future to the stub
        app_stub.validate_auth_token.return_value = validator_future

        # Create the base page handler
        base_page_handler = BasePageHandler(app_stub, MagicMock())

        # Call the bit of code we are testing
        validated = await base_page_handler.validate_auth_token('token')

        # Assert response from validate_auth_token is result of stubbed future
        assert validated is 'result_of_future'
        app_stub.validate_auth_token.assert_called_once_with('token')

    @pytest.mark.asyncio
    async def test_proxy_generate_auth_token_on_generate_auth_token(self):
        """Should proxy call to generate auth token to application generator."""

        # Create a stubbed version of the tornado app
        app_stub = MagicMock()

        # Create a stubbed future for the result of application.generate_auth_token()
        generator_future = asyncio.Future()
        generator_future.set_result('result_of_future')

        # Add the future to the stub
        app_stub.generate_auth_token.return_value = generator_future

        # Create the base page handler
        base_page_handler = BasePageHandler(app_stub, MagicMock())

        # Call the bit of code we are testing
        generated = await base_page_handler.generate_auth_token('user_id')

        # Assert response from generate_auth_token is result of stubbed future
        assert generated is 'result_of_future'
        app_stub.generate_auth_token.assert_called_once_with('user_id')


