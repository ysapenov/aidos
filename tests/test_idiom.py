from services.idiom_service import format_idiom_response


def test_format_idiom_response():
    data = {
        "idiom": "Break the ice",
        "literal_meaning": "Break frozen water.",
        "actual_meaning": "Start a conversation.",
        "russian_equivalent": "Растопить лёд",
        "kazakh_equivalent": "Мұзды бұзу",
        "example": "Break the ice.",
        "used_when": "People meet for the first time.",
        "similar_idioms": ["Get the ball rolling"],
    }

    result = format_idiom_response(data)

    assert "🎯 <b>Daily Idiom</b>" in result
    assert "<b>Break the ice</b>" in result
    assert "Meaning: <b>Start a conversation.</b>" in result
    assert "🇰🇿 Kazakh: Мұзды бұзу" in result
    assert "• Get the ball rolling" in result
