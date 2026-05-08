import os
import re
from typing import List, Dict

import requests

_NAVER_SEARCH_URL = "https://openapi.naver.com/v1/search/webkr.json"


def _strip_html(text: str) -> str:
    return re.sub(r"<[^>]+>", "", text).strip()


class NaverSearchAgent:
    """Naver 웹 검색 API를 호출하여 관련 웹 결과를 반환한다."""

    def run(self, payload: dict) -> dict:
        try:
            result = self._execute(payload)
            return {"success": True, "data": result, "error": None}
        except Exception as e:
            return {"success": False, "data": None, "error": str(e)}

    def _execute(self, payload: dict) -> dict:
        query: str = payload.get("query", "")
        display: int = payload.get("display", 5)

        if not query:
            raise ValueError("payload에 'query' 키가 필요합니다.")

        client_id = os.getenv("NAVER_CLIENT_ID")
        client_secret = os.getenv("NAVER_CLIENT_SECRET")
        if not client_id or not client_secret:
            raise EnvironmentError("NAVER_CLIENT_ID 또는 NAVER_CLIENT_SECRET 환경변수가 없습니다.")

        headers = {
            "X-Naver-Client-Id": client_id,
            "X-Naver-Client-Secret": client_secret,
        }
        params = {"query": query, "display": display, "sort": "sim"}
        res = requests.get(_NAVER_SEARCH_URL, headers=headers, params=params, timeout=10)
        res.raise_for_status()

        items = res.json().get("items", [])
        results: List[Dict] = [
            {
                "title": _strip_html(item.get("title", "")),
                "description": _strip_html(item.get("description", "")),
                "link": item.get("link") or item.get("originallink", ""),
            }
            for item in items
        ]
        return {"results": results}


if __name__ == "__main__":
    from dotenv import load_dotenv

    load_dotenv()
    agent = NaverSearchAgent()
    result = agent.run({"query": "RAG 시스템 구축 방법", "display": 3})
    if result["success"]:
        for item in result["data"]["results"]:
            print(f"제목: {item['title']}")
            print(f"설명: {item['description']}")
            print(f"링크: {item['link']}")
            print()
    else:
        print("오류:", result["error"])
