import asyncio
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from services.gemini_service import (
    parse_json_response,
    is_transient_error,
    call_with_retry,
    translate_word,
    generate_content,
)


def test_parse_json_response_valid():
    text = '{"key": "value"}'
    assert parse_json_response(text) == {"key": "value"}


def test_parse_json_response_markdown():
    text = '```json\n{"key": "value"}\n```'
    assert parse_json_response(text) == {"key": "value"}


def test_parse_json_response_invalid():
    text = "not json"
    with pytest.raises(ValueError):
        parse_json_response(text)


class DummyAPIError(Exception):
    def __init__(self, message: str, code: int | None = None, status: str | None = None):
        super().__init__(message)
        self.code = code
        self.status = status


def test_is_transient_error_codes():
    assert is_transient_error(DummyAPIError("Unavailable", code=503)) is True
    assert is_transient_error(DummyAPIError("Rate limited", code=429)) is True
    assert is_transient_error(DummyAPIError("Internal error", code=500)) is True
    assert is_transient_error(DummyAPIError("Bad Gateway", code=502)) is True
    assert is_transient_error(DummyAPIError("Gateway Timeout", code=504)) is True

    # Permanent client errors
    assert is_transient_error(DummyAPIError("Bad request", code=400)) is False
    assert is_transient_error(DummyAPIError("Unauthorized", code=401)) is False
    assert is_transient_error(DummyAPIError("Forbidden", code=403)) is False
    assert is_transient_error(DummyAPIError("Not found", code=404)) is False


def test_is_transient_error_status():
    assert is_transient_error(DummyAPIError("Server error", status="UNAVAILABLE")) is True
    assert is_transient_error(DummyAPIError("Quota exceeded", status="RESOURCE_EXHAUSTED")) is True
    assert is_transient_error(DummyAPIError("Deadline exceeded", status="DEADLINE_EXCEEDED")) is True
    assert is_transient_error(DummyAPIError("Internal error", status="INTERNAL")) is True


def test_is_transient_error_message_and_types():
    assert is_transient_error(Exception("503 UNAVAILABLE. This model is currently experiencing high demand.")) is True
    assert is_transient_error(asyncio.TimeoutError("Request timed out")) is True
    assert is_transient_error(ConnectionResetError("Connection lost")) is True
    assert is_transient_error(ValueError("Invalid argument format")) is False


@pytest.mark.asyncio
async def test_call_with_retry_immediate_success():
    mock_func = AsyncMock(return_value="success")

    result = await call_with_retry(mock_func, "arg1", max_retries=3, initial_delay=0.01)

    assert result == "success"
    assert mock_func.call_count == 1
    mock_func.assert_called_once_with("arg1")


@pytest.mark.asyncio
async def test_call_with_retry_transient_then_success():
    error_503 = DummyAPIError("High demand", code=503, status="UNAVAILABLE")
    mock_func = AsyncMock(side_effect=[error_503, "recovered"])

    with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
        result = await call_with_retry(mock_func, max_retries=3, initial_delay=0.1)

    assert result == "recovered"
    assert mock_func.call_count == 2
    assert mock_sleep.call_count == 1


@pytest.mark.asyncio
async def test_call_with_retry_exceeds_max_retries():
    error_503 = DummyAPIError("High demand", code=503, status="UNAVAILABLE")
    mock_func = AsyncMock(side_effect=error_503)

    with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
        with pytest.raises(DummyAPIError, match="High demand"):
            await call_with_retry(mock_func, max_retries=2, initial_delay=0.1)

    # 1 initial attempt + 2 retries = 3 calls
    assert mock_func.call_count == 3
    assert mock_sleep.call_count == 2


@pytest.mark.asyncio
async def test_call_with_retry_non_transient_fails_immediately():
    error_400 = DummyAPIError("Bad request", code=400)
    mock_func = AsyncMock(side_effect=error_400)

    with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
        with pytest.raises(DummyAPIError, match="Bad request"):
            await call_with_retry(mock_func, max_retries=3, initial_delay=0.1)

    # Should not retry at all on 400
    assert mock_func.call_count == 1
    mock_sleep.assert_not_called()


@pytest.mark.asyncio
async def test_translate_word_with_retry():
    mock_response = MagicMock()
    mock_response.text = '{"word": "apple", "russian": "яблоко"}'

    error_503 = DummyAPIError("High demand", code=503, status="UNAVAILABLE")
    mock_generate = AsyncMock(side_effect=[error_503, mock_response])

    mock_client = MagicMock()
    mock_client.aio.models.generate_content = mock_generate

    with patch("services.gemini_service._get_client", return_value=mock_client):
        with patch("asyncio.sleep", new_callable=AsyncMock):
            result = await translate_word("apple")

    assert result == {"word": "apple", "russian": "яблоко"}
    assert mock_generate.call_count == 2


@pytest.mark.asyncio
async def test_generate_content_with_retry():
    mock_response = MagicMock()
    mock_response.text = "Hello world!"

    mock_client = MagicMock()
    mock_client.aio.models.generate_content = AsyncMock(return_value=mock_response)

    with patch("services.gemini_service._get_client", return_value=mock_client):
        result = await generate_content("Say hello")

    assert result == "Hello world!"
    mock_client.aio.models.generate_content.assert_called_once()

