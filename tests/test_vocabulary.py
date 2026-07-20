from services.vocabulary_service import format_vocabulary_response


def test_format_vocabulary_response():
    data = {
        "topic": "Business",
        "words": [
            {
                "english": "meticulous",
                "ipa": "/məˈtɪkjələs/",
                "part_of_speech": "adjective",
                "cefr_level": "C1",
                "definition": "Showing great attention to detail.",
                "russian": "Скрупулёзный",
                "kazakh": "Ұқыпты",
                "example": "She is meticulous.",
                "collocations": ["meticulous planning"],
                "synonyms": ["thorough"],
            }
        ],
        "phrasal_verbs": [
            {
                "english": "carry out",
                "meaning": "To perform or complete something.",
                "russian": "Выполнять",
                "kazakh": "Орындау",
                "example": "Carry out a test.",
                "used_in": ["research"],
                "related": ["perform"],
            }
        ],
        "expressions": [
            {
                "english": "rings a bell",
                "meaning": "Sounds familiar.",
                "russian": "Знакомо",
                "kazakh": "Есіме түсіп тұрғандай",
                "example": "It rings a bell.",
                "used_when": "remembering",
                "formality": "Neutral",
                "similar": ["familiar"],
            }
        ],
    }

    result = format_vocabulary_response(data)

    assert "🎯 <b>Topic:</b> Business" in result
    assert "<b>meticulous</b> /məˈtɪkjələs/ <i>(adjective, C1)</i>" in result
    assert "🇰🇿 Kazakh: Ұқыпты" in result
    assert "<b>carry out</b>" in result
    assert "🇰🇿 Kazakh: Орындау" in result
    assert "<b>rings a bell</b>" in result
    assert "🇰🇿 Kazakh: Есіме түсіп тұрғандай" in result
