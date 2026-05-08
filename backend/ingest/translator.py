import json
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List

from openai import OpenAI

_MODEL = "gpt-4o-mini"

_SYSTEM_PROMPT = (
    "You are a translator. "
    "You will receive a JSON array of strings. "
    "Translate each string to English. If a string is already in English, return it unchanged. "
    "Return ONLY a valid JSON array of translated strings in the same order. "
    "No explanations, no markdown, no extra text."
)


def _get_client() -> OpenAI:
    return OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def translate_to_english(text: str) -> str:
    """단일 텍스트를 영어로 번역한다."""
    results = translate_texts_to_english([text])
    return results[0]


def _translate_batch(batch: List[str]) -> List[str]:
    """여러 텍스트를 한 번의 API 호출로 번역한다."""
    if not batch:
        return []

    client = _get_client()
    response = client.chat.completions.create(
        model=_MODEL,
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": json.dumps(batch, ensure_ascii=False)},
        ],
        max_tokens=4096,
        response_format={"type": "json_object"},
    )
    raw = response.choices[0].message.content.strip()

    # {"translations": [...]} 또는 {"result": [...]} 형태 모두 허용
    parsed = json.loads(raw)
    if isinstance(parsed, list):
        translated = parsed
    else:
        translated = next(v for v in parsed.values() if isinstance(v, list))

    # 길이 불일치 시 원본 반환
    if len(translated) != len(batch):
        return batch
    return translated


def translate_texts_to_english(texts: List[str], batch_size: int = 20, max_workers: int = 10) -> List[str]:
    """텍스트 목록을 배치 묶음 + 병렬 실행으로 빠르게 영어로 번역한다."""
    if not texts:
        return []

    batches = [texts[i : i + batch_size] for i in range(0, len(texts), batch_size)]
    results: List[str | None] = [None] * len(texts)

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(_translate_batch, batch): i for i, batch in enumerate(batches)}
        for future in as_completed(futures):
            batch_idx = futures[future]
            try:
                batch_results = future.result()
            except Exception:
                # 번역 실패 시 해당 배치는 원본 그대로 사용
                batch_results = batches[batch_idx]
            start = batch_idx * batch_size
            for j, text in enumerate(batch_results):
                results[start + j] = text

    return results


if __name__ == "__main__":
    from dotenv import load_dotenv

    load_dotenv()
    samples = [
        "안녕하세요. 이 문서는 사내 규정집입니다.",
        "REM sleep is a phase of the sleep cycle.",
        "출장 신청은 최소 3일 전에 제출해야 합니다.",
        "제품명: 세럼A, 성분: 레티놀, 용량: 30ml",
    ]
    translated = translate_texts_to_english(samples)
    for orig, tr in zip(samples, translated):
        print(f"원본: {orig}")
        print(f"번역: {tr}")
        print()
