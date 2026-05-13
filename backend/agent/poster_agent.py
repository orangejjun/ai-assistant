import base64
import os
from typing import Dict, List

from openai import OpenAI

from backend.retrieval.retrieval_agent import RetrievalAgent

_GPT_MODEL = "gpt-4o-mini"
_IMAGE_MODEL = "gpt-image-1"

_PROMPT_SYSTEM = (
    "You are a senior art director specializing in Korean beauty (K-beauty) brand marketing. "
    "Given a topic and reference document excerpts from a cosmetics company, "
    "write an image generation prompt for a premium 2D digital poster or marketing graphic. "
    "Design guidelines: "
    "1) Style — flat 2D digital graphic, clean and elegant, NO 3D mockups, NO physical props. "
    "2) Aesthetic — K-beauty premium: soft and sophisticated. "
    "   Use color palettes such as: ivory/cream white, blush pink, champagne gold, sage green, "
    "   lavender, or deep navy depending on the product theme. "
    "3) Layout — clear visual hierarchy: bold headline area, key benefit callouts, "
    "   decorative botanical or geometric accents, ample white space. "
    "4) Typography — elegant sans-serif or thin serif typefaces implied in the design. "
    "5) Forbidden — no shadows, no photo-realism, no physical paper, no room/environment, "
    "   no binder clips, no mockup frames. Content must fill 100% of the canvas edge-to-edge. "
    "Write the prompt in English. Start with: "
    "'Flat 2D digital K-beauty brand poster, edge-to-edge design, no mockup, no shadows,'"
)


class PosterAgent:
    """문서 청크를 기반으로 gpt-image-1 포스터 이미지를 생성한다."""

    def run(self, payload: dict) -> dict:
        try:
            result = self._execute(payload)
            return {"success": True, "data": result, "error": None}
        except Exception as e:
            return {"success": False, "data": None, "error": str(e)}

    def _execute(self, payload: dict) -> dict:
        topic: str = payload.get("topic", "")
        size: str = payload.get("size", "1024x1536")
        if not topic:
            raise ValueError("payload에 'topic' 키가 필요합니다.")

        chunks = self._retrieve(topic)
        image_prompt = self._build_image_prompt(topic, chunks)
        image_b64 = self._generate_image(image_prompt, size)
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

    def _generate_image(self, prompt: str, size: str = "1024x1536") -> str:
        enforced = (
            "Flat 2D digital K-beauty brand poster, edge-to-edge design, no mockup, no shadows. "
            "Pure flat background filling 100% of the canvas edge-to-edge. "
            "NO shadows, NO photo-realistic rendering, NO 3D perspective, "
            "NO paper texture, NO binder clips, NO wall, NO room, NO mockup frame, "
            "NO border, NO margins, NO surrounding environment, NO physical objects. "
            "Premium Korean beauty brand aesthetic: soft sophisticated color palette, "
            "elegant typography layout, botanical or geometric decorative accents, ample white space. "
            "Content must touch all four edges of the image. "
            + prompt
            + " Completely flat 2D K-beauty digital graphic. Pure premium cosmetics brand design."
        )
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        response = client.images.generate(
            model=_IMAGE_MODEL,
            prompt=enforced,
            size=size,
            quality="high",
            n=1,
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
