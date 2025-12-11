import os
import re
import json
import pandas as pd
from dotenv import load_dotenv
from openai import OpenAI

# =========================
# 환경 변수 / 기본 설정
# =========================
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY 가 설정되어 있지 않습니다. .env 를 확인하세요.")

client = OpenAI(api_key=OPENAI_API_KEY)

EXCEL_PATH = "products.xlsx"
OUTPUT_DIR = "site_products"

REQUIRED_COLUMNS = [
    "no",
    "productName",
    "productUrl",
    "mainImage",
    "shortTitle",
    "productDescription",
]


# =========================
# slug 유틸 (파일명용)
# =========================
def slugify(text: str) -> str:
    text = str(text).strip()
    # 한글/영문/숫자만 남기고 나머지는 - 로 치환
    text = re.sub(r"[^0-9a-zA-Z가-힣]+", "-", text)
    text = re.sub(r"-{2,}", "-", text).strip("-")
    if not text:
        text = "product"
    return text[:40]


# =========================
# GPT: 소개 문단 + 스펙 표 데이터 생성
# =========================
def generate_intro_and_specs(name: str, desc: str) -> tuple[str, list[dict]]:
    """
    상품명 / 한 줄 설명을 기반으로:
      - intro: 1~2문장 소개
      - rows: [{"label": "소재", "detail": "…" }, ...]
    를 JSON 으로 받아서 반환.
    """
    if not name and not desc:
        return "", []

    system_msg = (
        "너는 한국 온라인 쇼핑몰 상세페이지를 요약해서 "
        "블로그/랜딩 페이지용 소개글을 만드는 마케터야.\n"
        "다음 규칙을 반드시 지켜라.\n"
        "1) intro: 1~2문장, 80자 이내. 고객의 상황을 공감하면서 상품의 장점을 짧게 요약.\n"
        "2) rows: 표로 정리할 핵심 스펙 5~8개.\n"
        "   - label 예시: 소재, 방수 여부, 방한 기능, 사용 대상, 디자인, 무게, 계절, 내구성 등.\n"
        "   - 상품 특성에 맞게 자유롭게 label 을 정해도 됨.\n"
        "3) 반드시 아래 JSON 형식 '한 줄'로만 출력:\n"
        "{"
        "\"intro\": \"...\", "
        "\"rows\": ["
        "{\"label\": \"소재\", \"detail\": \"...\"}, "
        "{\"label\": \"방수 여부\", \"detail\": \"...\"}"
        "]"
        "}"
    )

    user_msg = (
        f"상품명: {name}\n"
        f"간단 설명(있으면): {desc}\n\n"
        "위 정보를 참고해서 intro와 rows 를 JSON 으로 만들어줘."
    )

    resp = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {"role": "system", "content": system_msg},
            {"role": "user", "content": user_msg},
        ],
        max_tokens=400,
    )

    text = resp.choices[0].message.content.strip()

    # 코드블럭 처리
    if text.startswith("```"):
        text = text.strip("`")
        lines = text.splitlines()
        if lines and "{" not in lines[0]:
            text = "\n".join(lines[1:])
        text = text.strip()

    try:
        data = json.loads(text)
    except Exception:
        # 실패 시 최소 fallback
        return desc or "", []

    intro = str(data.get("intro", "")).strip()
    rows = data.get("rows", []) or []

    # rows 가 형식이 이상하면 정리
    cleaned_rows = []
    for r in rows:
        label = str(r.get("label", "")).strip()
        detail = str(r.get("detail", "")).strip()
        if label and detail:
            cleaned_rows.append({"label": label, "detail": detail})

    return intro, cleaned_rows


# =========================
# 개별 상품 Markdown 생성
# =========================
def build_markdown(
    no: int,
    name: str,
    short_title: str,
    product_url: str,
    image_url: str,
    intro: str,
    rows: list[dict],
) -> str:
    """
    - 상단 YAML front matter
    - 제목 + 이미지
    - 소개 문단
    - 스펙 표 (| 구분 | 상세 설명 |)
    - 빨간 CTA 박스 + 링크
    """

    display_title = short_title or name
    heading = f"{no}번. {display_title}"

    lines: list[str] = []

    # --- YAML front matter ---
    lines.append("---")
    lines.append(f'title: "{display_title}"')
    lines.append(f"product_no: {no}")
    lines.append(f'product_name: "{name}"')
    lines.append(f'product_url: "{product_url}"')
    lines.append(f'image_url: "{image_url}"')
    lines.append("---")
    lines.append("")

    # --- 본문 ---
    lines.append(f"# {heading}")
    lines.append("")

    if image_url:
        lines.append(f"![{display_title}]({image_url})")
        lines.append("")

    if intro:
        lines.append(intro)
        lines.append("")

    # 스펙 표
    if rows:
        lines.append("| 구분 | 상세 설명 |")
        lines.append("| --- | --- |")
        for r in rows:
            label = r["label"].replace("|", "\\|")
            detail = r["detail"].replace("|", "\\|")
            lines.append(f"| {label} | {detail} |")
        lines.append("")
    else:
        # rows 가 없을 때 최소한 기본 설명이라도
        lines.append("상세 스펙은 판매 페이지에서 확인해 주세요.")
        lines.append("")

    # 🔥 CTA 박스 (빨간 테두리 박스)
    if product_url:
        lines.append(
            '<div style="margin-top:18px;padding:18px;border:2px solid #ff4d4f;'
            'border-radius:14px;background:#fff7f6;text-align:center;'
            'font-weight:600;color:#ff4d4f;font-size:15px;line-height:1.6;">'
        )
        lines.append("🔥 놓치면 후회할 가격!<br/>")
        lines.append(
            f'<a href="{product_url}" '
            'style="color:#0052cc;text-decoration:none;font-weight:700;">'
            "지금 바로 최저가 확인하기 →"
            "</a>"
        )
        lines.append("</div>")
        lines.append("")

    return "\n".join(lines)


# =========================
# index.md (목차) 생성
# =========================
def build_index_markdown(items: list[dict]) -> str:
    """
    items: [{"no": 1, "title": "...", "filename": "product_001_....md"}, ...]
    """
    lines: list[str] = []

    lines.append("---")
    lines.append('title: "상품 모아보기"')
    lines.append("---")
    lines.append("")
    lines.append("# 하진팜 상품 모아보기")
    lines.append("")
    lines.append("인스타그램 프로필 링크에서 보신 상품 번호를 그대로 검색하신 뒤,")
    lines.append("아래 목록에서 해당 상품을 선택해 자세한 정보를 확인해 보세요.")
    lines.append("")

    for item in sorted(items, key=lambda x: x["no"]):
        no = item["no"]
        title = item["title"]
        filename = item["filename"]
        lines.append(f"- [{no}번. {title}](./{filename})")

    lines.append("")
    return "\n".join(lines)


# =========================
# 메인
# =========================
def main():
    if not os.path.exists(EXCEL_PATH):
        raise FileNotFoundError(f"엑셀 파일을 찾을 수 없습니다: {EXCEL_PATH}")

    df = pd.read_excel(EXCEL_PATH)

    if df.empty:
        raise RuntimeError("products.xlsx 에 데이터가 없습니다.")

    for col in REQUIRED_COLUMNS:
        if col not in df.columns:
            raise RuntimeError(f"엑셀에 필요한 컬럼이 없습니다: {col}")

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    index_items: list[dict] = []

    for _, row in df.iterrows():
        try:
            no = int(row["no"])
        except Exception:
            continue

        name = str(row.get("productName", "")).strip()
        product_url = str(row.get("productUrl", "")).strip()
        main_image = str(row.get("mainImage", "")).strip()
        short_title = str(row.get("shortTitle", "")).strip()
        base_desc = str(row.get("productDescription", "")).strip()

        if not name or not product_url:
            # 필수 정보 없으면 건너뜀
            continue

        # GPT 로 intro + 스펙 표 데이터 생성
        intro, rows = generate_intro_and_specs(name, base_desc)

        # 마크다운 본문 생성
        md_content = build_markdown(
            no=no,
            name=name,
            short_title=short_title,
            product_url=product_url,
            image_url=main_image,
            intro=intro,
            rows=rows,
        )

        slug = slugify(short_title or name)
        filename = f"product_{no:03d}_{slug}.md"
        filepath = os.path.join(OUTPUT_DIR, filename)

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(md_content)

        index_items.append(
            {
                "no": no,
                "title": short_title or name,
                "filename": filename,
            }
        )

        print(f"[MD] 상품 {no}번 → {filepath} 생성 완료")

    # index.md 생성
    index_md = build_index_markdown(index_items)
    index_path = os.path.join(OUTPUT_DIR, "index.md")
    with open(index_path, "w", encoding="utf-8") as f:
        f.write(index_md)

    print(f"[MD] 목차 페이지 생성 완료: {index_path}")


if __name__ == "__main__":
    main()