import pytest
from utils.formatting import escape_html, format_translation, format_history, format_users_list

def test_escape_html():
    assert escape_html("<b>hello</b>") == "&lt;b&gt;hello&lt;/b&gt;"
    assert escape_html("test & test") == "test &amp; test"

def test_format_translation():
    data = {
        "pronunciation": "[test]",
        "translations": [{"russian": "тест", "meaning": "испытание"}],
        "kazakh": "сынақ",
        "part_of_speech": "noun",
        "examples": [{"english": "A test.", "russian": "Тест."}],
        "collocations": [{"english": "run a test", "russian": "провести тест"}]
    }
    result = format_translation("test", data)
    assert "<b>test</b>" in result
    assert "🗣️ Pronunciation: [test]" in result
    assert "тест — испытание" in result
    assert "Kazakh: сынақ" in result

def test_format_translation_error():
    data = {"error": "Not found"}
    result = format_translation("unknown", data)
    assert "Not found" in result

def test_format_history():
    entries = [
        {
            "word": "apple",
            "translation": '{"translations": [{"russian": "яблоко"}]}',
            "created_at": "2026-07-20T12:00:00",
            "kazakh_translation": "алма"
        }
    ]
    result = format_history(entries, 1)
    assert "apple" in result
    assert "яблоко" in result
    assert "алма" in result
    assert "Jul 20" in result

def test_format_history_empty():
    assert format_history([], 0) == ""

def test_format_users_list():
    static = {123}
    db_users = [{"telegram_id": 456, "username": "test", "first_name": "Test User"}]
    result = format_users_list(db_users, static)
    assert "123" in result
    assert "456" in result
    assert "@test" in result
