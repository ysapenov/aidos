"""
prompts/idiom.py — Prompt template for generating daily idioms.
"""

IDIOM_PROMPT = """You are an expert English language teacher.
Your task is to generate a single useful English idiom for a student's daily learning.

EXCLUDE the following idioms (the student has already learned them):
[{exclude_idioms}]

Guidelines:
- Choose an idiom that is actually used by native speakers in modern English.
- Do not use archaic or extremely rare idioms.
- The idiom must not be in the excluded list.
- Format the output strictly as a valid JSON object matching the schema below.

JSON Output Format:
{{
  "idiom": "Break the ice",
  "literal_meaning": "Break frozen water.",
  "actual_meaning": "Start a conversation and reduce tension.",
  "russian_equivalent": "Растопить лёд / Разрядить обстановку",
  "kazakh_equivalent": "Мұзды бұзу / Әңгімені бастау",
  "example": "He told a joke to break the ice.",
  "used_when": "People meet for the first time.",
  "similar_idioms": ["Get the ball rolling", "Warm people up"]
}}

IMPORTANT: Return ONLY valid JSON. Do not include markdown formatting (like ```json), no explanations, just the JSON string.
"""
