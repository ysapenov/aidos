import pytest
from services.gemini_service import parse_json_response


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
