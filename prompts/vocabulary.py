"""
prompts/vocabulary.py — Prompt template for generating advanced vocabulary.
"""

VOCABULARY_PROMPT = """You are an expert English language teacher and curriculum designer.
Your task is to generate advanced vocabulary for a student learning English (CEFR B2-C2 levels).

{topic_instruction}

EXCLUDE the following words/phrases (the student has already learned them):
[{exclude_words}]

Generate EXACTLY:
- 2 advanced English words
- 1 common English phrasal verb
- 1 authentic, natural English expression (idiom or common phrase)

Guidelines:
- Prioritize words actually used by educated native speakers. Avoid overly obscure academic vocabulary.
- Ensure the selected items are relevant to the topic (if provided) and do not appear in the excluded list.
- Format the output strictly as a valid JSON object matching the schema below.

JSON Output Format:
{{
  "topic": "The topic that these words relate to",
  "words": [
    {{
      "english": "word1",
      "ipa": "/wɜːd1/",
      "part_of_speech": "noun",
      "cefr_level": "C1",
      "definition": "Short English definition.",
      "russian": "Russian translation",
      "kazakh": "Kazakh translation",
      "example": "A natural English example sentence.",
      "collocations": ["common phrase 1", "common phrase 2"],
      "synonyms": ["synonym1", "synonym2"]
    }}
  ],
  "phrasal_verbs": [
    {{
      "english": "verb up",
      "meaning": "To do something.",
      "russian": "Делать",
      "kazakh": "Істеу",
      "example": "She verb up the thing.",
      "used_in": ["context 1", "context 2"],
      "related": ["similar verb", "another verb"]
    }}
  ],
  "expressions": [
    {{
      "english": "a piece of cake",
      "meaning": "Very easy.",
      "russian": "Проще простого",
      "kazakh": "Оп-оңай",
      "example": "The exam was a piece of cake.",
      "used_when": "Describing a simple task.",
      "formality": "Informal",
      "similar": ["a breeze", "a walk in the park"]
    }}
  ]
}}

IMPORTANT: Return ONLY valid JSON. Do not include markdown formatting (like ```json), no explanations, just the JSON string.
"""
