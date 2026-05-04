import os
from typing import List

from openai import OpenAI

_MODEL = "gpt-4o-mini"

_SYSTEM_PROMPT = (
    "You are a translator. "
    "Detect the language of the input text. "
    "If it is already in English, return it unchanged. "
    "Otherwise, translate it to English accurately. "
    "Return only the translated text with no explanations or commentary."
)


def _get_client() -> OpenAI:
    return OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def translate_to_english(text: str) -> str:
    """텍스트를 영어로 번역한다. 이미 영어이면 그대로 반환한다."""
    if not text.strip():
        return text

    client = _get_client()
    response = client.chat.completions.create(
        model=_MODEL,
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": text},
        ],
        max_tokens=2048,
    )
    return response.choices[0].message.content.strip()


def translate_texts_to_english(texts: List[str]) -> List[str]:
    """텍스트 목록을 순서대로 영어로 번역한다."""
    return [translate_to_english(t) for t in texts]


if __name__ == "__main__":
    from dotenv import load_dotenv

    load_dotenv()
    samples = [
        "안녕하세요. 이 문서는 사내 규정집입니다.",
        "REM sleep is a phase of the sleep cycle.",
        "출장 신청은 최소 3일 전에 제출해야 합니다.",
    ]
    for s in samples:
        print(f"원본: {s}")
        print(f"번역: {translate_to_english(s)}")
        print()
