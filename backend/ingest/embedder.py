import os
from typing import List

from openai import OpenAI

EMBED_MODEL = "text-embedding-3-small"
BATCH_SIZE = 100


def embed_texts(texts: List[str]) -> List[List[float]]:
    """
    텍스트 리스트를 임베딩 벡터 리스트로 변환한다.
    BATCH_SIZE 단위로 나누어 API를 호출한다.

    Args:
        texts: 임베딩할 텍스트 목록

    Returns:
        List[List[float]]: 입력 순서와 동일하게 대응하는 임베딩 벡터
    """
    if not texts:
        return []

    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    embeddings: List[List[float]] = []

    for i in range(0, len(texts), BATCH_SIZE):
        batch = texts[i : i + BATCH_SIZE]
        response = client.embeddings.create(model=EMBED_MODEL, input=batch)
        # index 기준으로 정렬해 입력 순서를 보장한다
        batch_vecs = [item.embedding for item in sorted(response.data, key=lambda x: x.index)]
        embeddings.extend(batch_vecs)
        print(f"  [EMBED] 배치 {i // BATCH_SIZE + 1} 완료 ({len(batch)}개)")

    return embeddings


if __name__ == "__main__":
    from dotenv import load_dotenv

    load_dotenv()

    samples = [
        "안녕하세요, 임베딩 테스트입니다.",
        "두 번째 테스트 문장입니다.",
        "OpenAI text-embedding-3-small 모델을 사용합니다.",
    ]
    vecs = embed_texts(samples)
    print(f"\n임베딩 완료: {len(vecs)}개, 차원: {len(vecs[0])}")
    print(f"첫 번째 벡터 앞 5개 값: {vecs[0][:5]}")
