import base64
import os
from typing import Dict, List

from openai import OpenAI

from backend.retrieval.retrieval_agent import RetrievalAgent

_GPT_MODEL = "gpt-4o-mini"
_IMAGE_MODEL = "dall-e-3"
_IMAGE_SIZE = "1024x1792"

_PROMPT_SYSTEM = (
    "You are a professional graphic designer creating flat 2D digital infographics. "
    "Given a topic and reference document excerpts, write a DALL-E prompt for a digital infographic layout (NOT a photo of a poster). "
    "The prompt must start with: "
    "'Flat 2D digital infographic design, top-down view, no mockup, no shadows, no physical paper, pure digital artwork,' "
    "Then describe: visual style, color scheme, title placement, key sections, icons or illustrations, and typography. "
    "Write the prompt in English regardless of the input language."
)


class PosterAgent:
    """문서 청크를 기반으로 gpt-image-2 포스터 이미지를 생성한다."""

    def run(self, payload: dict) -> dict:
        try:
            result = self._execute(payload)
            return {"success": True, "data": result, "error": None}
        except Exception as e:
            return {"success": False, "data": None, "error": str(e)}

    def _execute(self, payload: dict) -> dict:
        topic: str = payload.get("topic", "")
        if not topic:
            raise ValueError("payload에 'topic' 키가 필요합니다.")

        chunks = self._retrieve(topic)
        image_prompt = self._build_image_prompt(topic, chunks)
        image_b64 = self._generate_image(image_prompt)
        sources = list(dict.fromkeys(c["source_file"] for c in chunks))

        return {
            "image_b64": image_b64,
            "topic": topic,
            "prompt_used": image_prompt,
            "sources": sources,
        }

    def _retrieve(self, topic: str) -> List[Dict]:
        agent = RetrievalAgent()
        result = agent.run({"query": topic, "k": 5})
        if not result["success"]:
            return []
        return result["data"]["chunks"]

    def _build_image_prompt(self, topic: str, chunks: List[Dict]) -> str:
        context = "\n\n".join(
            f"[Excerpt {i}]\n{c['chunk_text'][:600]}"
            for i, c in enumerate(chunks, 1)
        )
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        response = client.chat.completions.create(
            model=_GPT_MODEL,
            max_tokens=1536,
            messages=[
                {"role": "system", "content": _PROMPT_SYSTEM},
                {
                    "role": "user",
                    "content": (
                        f"Topic: {topic}\n\n"
                        f"Reference documents:\n{context}\n\n"
                        "Write an image generation prompt for a flat digital graphic (infographic)."
                    ),
                },
            ],
        )
        return response.choices[0].message.content.strip()

    def _generate_image(self, prompt: str) -> str:
        enforced = (
            "Flat digital graphic design artwork, infographic style. "
            "Pure background filling 100% of the canvas. "
            "NO shadows, NO photo-realistic rendering, NO 3D perspective, "
            "NO paper texture, NO binder clips, NO wall, NO room, NO mockup, "
            "NO frame, NO border, NO margins, NO surrounding environment. "
            "This is a 2D vector-style flat digital graphic viewed perfectly straight-on. "
            "The content must touch all four edges of the image. "
            + prompt
            + " Completely flat digital graphic design. No depth, no shadow, no physical object. "
            "Pure 2D infographic filling the entire canvas."
        )
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        response = client.images.generate(
            model=_IMAGE_MODEL,
            prompt=enforced,
            size=_IMAGE_SIZE,
            quality="hd",
            n=1,
            response_format="b64_json",
        )
        return response.data[0].b64_json


if __name__ == "__main__":
    from dotenv import load_dotenv

    load_dotenv()
    agent = PosterAgent()
    result = agent.run({"topic": "REM sleep"})
    if result["success"]:
        print("이미지 생성 완료, base64 길이:", len(result["data"]["image_b64"]))
    else:
        print("오류:", result["error"])
