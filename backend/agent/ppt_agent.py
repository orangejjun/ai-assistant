import base64
import io
import json
import os
from typing import Dict, List

from openai import OpenAI
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.util import Inches, Pt

from backend.retrieval.retrieval_agent import RetrievalAgent

_GPT_MODEL = "gpt-4o-mini"
_MAX_TOKENS = 4096
_DEFAULT_SLIDES = 5

_C_BG = RGBColor(0xF9, 0xFA, 0xFB)
_C_TITLE = RGBColor(0x19, 0x1F, 0x28)
_C_ACCENT = RGBColor(0x31, 0x82, 0xF6)
_C_BODY = RGBColor(0x4E, 0x5B, 0x6A)
_C_WHITE = RGBColor(0xFF, 0xFF, 0xFF)

_SYSTEM_PROMPT = """You are a professional presentation designer.
Given a topic and reference document excerpts, generate slide content as JSON.

Rules:
- First slide must be type "title" (title + subtitle)
- Then content slides (type "content"): title (max 8 words) + 4-5 bullet points (max 15 words each)
- Last slide must be type "summary": title "Summary" + 4-5 key takeaway bullets
- Write content in the same language as the topic
- Respond ONLY with valid JSON, no markdown fences

JSON format:
{
  "title": "Presentation Title",
  "slides": [
    {"type": "title", "title": "...", "subtitle": "..."},
    {"type": "content", "title": "...", "bullets": ["...", "..."]},
    {"type": "summary", "title": "Summary", "bullets": ["...", "..."]}
  ]
}"""


class PptAgent:
    """사내 문서 기반으로 PowerPoint(.pptx) 프레젠테이션을 생성하는 에이전트."""

    def run(self, payload: dict) -> dict:
        try:
            result = self._execute(payload)
            return {"success": True, "data": result, "error": None}
        except Exception as e:
            return {"success": False, "data": None, "error": str(e)}

    def _execute(self, payload: dict) -> dict:
        topic: str = payload.get("topic", "")
        num_slides: int = int(payload.get("num_slides", _DEFAULT_SLIDES))
        if not topic:
            raise ValueError("payload에 'topic' 키가 필요합니다.")

        chunks = self._retrieve(topic)
        slides_data = self._build_slides(topic, chunks, num_slides)
        pptx_b64 = self._generate_pptx(slides_data)
        sources = list(dict.fromkeys(c["source_file"] for c in chunks if c.get("source_file")))

        return {
            "presentation_b64": pptx_b64,
            "topic": topic,
            "slide_count": len(slides_data["slides"]),
            "slides": slides_data["slides"],
            "sources": sources,
        }

    def _retrieve(self, query: str) -> List[Dict]:
        agent = RetrievalAgent()
        result = agent.run({"query": query, "k": 5})
        if not result["success"]:
            return []
        return result["data"]["chunks"]

    def _build_slides(self, topic: str, chunks: List[Dict], num_slides: int) -> dict:
        context = "\n\n".join(
            f"[Excerpt {i}]\n{c['chunk_text'][:600]}"
            for i, c in enumerate(chunks, 1)
        )
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        response = client.chat.completions.create(
            model=_GPT_MODEL,
            max_tokens=_MAX_TOKENS,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": (
                        f"Topic: {topic}\n"
                        f"Target number of slides (excluding title): {num_slides}\n\n"
                        f"Reference documents:\n{context}\n\n"
                        "Generate the presentation JSON."
                    ),
                },
            ],
        )
        return json.loads(response.choices[0].message.content)

    def _generate_pptx(self, slides_data: dict) -> str:
        prs = Presentation()
        prs.slide_width = Inches(13.33)
        prs.slide_height = Inches(7.5)

        for slide_info in slides_data.get("slides", []):
            if slide_info.get("type") == "title":
                self._add_title_slide(prs, slide_info, slides_data.get("title", ""))
            else:
                self._add_content_slide(prs, slide_info)

        buf = io.BytesIO()
        prs.save(buf)
        return base64.b64encode(buf.getvalue()).decode("utf-8")

    def _add_title_slide(self, prs: Presentation, info: dict, prs_title: str) -> None:
        slide = prs.slides.add_slide(prs.slide_layouts[6])  # 빈 레이아웃
        self._fill_bg(slide, _C_ACCENT)

        # 제목
        title_box = slide.shapes.add_textbox(Inches(1.2), Inches(2.2), Inches(10.9), Inches(1.8))
        tf = title_box.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = info.get("title") or prs_title
        p.font.size = Pt(40)
        p.font.bold = True
        p.font.color.rgb = _C_WHITE

        # 부제목
        subtitle = info.get("subtitle", "")
        if subtitle:
            sub_box = slide.shapes.add_textbox(Inches(1.2), Inches(4.2), Inches(10.9), Inches(1.2))
            tf2 = sub_box.text_frame
            tf2.word_wrap = True
            p2 = tf2.paragraphs[0]
            p2.text = subtitle
            p2.font.size = Pt(22)
            p2.font.color.rgb = RGBColor(0xD1, 0xE8, 0xFF)

    def _add_content_slide(self, prs: Presentation, info: dict) -> None:
        slide = prs.slides.add_slide(prs.slide_layouts[6])  # 빈 레이아웃
        self._fill_bg(slide, _C_BG)

        # 상단 강조 바
        from pptx.util import Emu
        bar = slide.shapes.add_shape(
            1,  # MSO_SHAPE_TYPE.RECTANGLE
            Inches(0), Inches(0), prs.slide_width, Inches(0.08)
        )
        bar.fill.solid()
        bar.fill.fore_color.rgb = _C_ACCENT
        bar.line.fill.background()

        # 슬라이드 제목
        title_box = slide.shapes.add_textbox(Inches(0.6), Inches(0.25), Inches(12.1), Inches(0.9))
        tf = title_box.text_frame
        p = tf.paragraphs[0]
        p.text = info.get("title", "")
        p.font.size = Pt(28)
        p.font.bold = True
        p.font.color.rgb = _C_TITLE

        # 구분선
        from pptx.util import Pt as PtUtil
        line = slide.shapes.add_shape(1, Inches(0.6), Inches(1.25), Inches(12.1), Inches(0.03))
        line.fill.solid()
        line.fill.fore_color.rgb = _C_ACCENT
        line.line.fill.background()

        # 불릿 포인트
        bullets = info.get("bullets", [])
        body_box = slide.shapes.add_textbox(Inches(0.8), Inches(1.5), Inches(11.7), Inches(5.6))
        tf2 = body_box.text_frame
        tf2.word_wrap = True
        for i, bullet in enumerate(bullets):
            if i == 0:
                p = tf2.paragraphs[0]
            else:
                p = tf2.add_paragraph()
            p.text = f"• {bullet}"
            p.font.size = Pt(20)
            p.font.color.rgb = _C_BODY
            p.space_after = Pt(10)

    def _fill_bg(self, slide, color: RGBColor) -> None:
        bg = slide.background
        fill = bg.fill
        fill.solid()
        fill.fore_color.rgb = color


if __name__ == "__main__":
    from dotenv import load_dotenv

    load_dotenv()
    agent = PptAgent()
    result = agent.run({"topic": "가격 정책 변경 보고", "num_slides": 4})
    if result["success"]:
        d = result["data"]
        print(f"슬라이드 수: {d['slide_count']}")
        for s in d["slides"]:
            print(f"  [{s['type']}] {s.get('title', '')}")
        with open("/tmp/test_output.pptx", "wb") as f:
            f.write(base64.b64decode(d["presentation_b64"]))
        print("저장됨: /tmp/test_output.pptx")
    else:
        print(f"오류: {result['error']}")
