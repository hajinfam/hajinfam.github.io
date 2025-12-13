import os
import re
import json
import pandas as pd
from dotenv import load_dotenv
from openai import OpenAI

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

# ---------------------------------------
# 기존 md 파일의 front matter 간단 파싱
# ---------------------------------------
FM_RE = re.compile(r"^---\s*(.*?)\s*---\s*", re.DOTALL)

def parse_front_matter(md_text: str) -> dict:
    m = FM_RE.match(md_text)
    if not m:
        return {}
    block = m.group(1)
    data = {}
    for line in block.splitlines():
        line = line.strip()
        if not line or ":" not in line:
            continue
        k, v = line.split(":", 1)
        data[k.strip()] = v.strip().strip('"')
    return data

def is_md_good_enough(existing_md: str, expected_no: int, expected_url: str) -> bool:
    """
    '이미 제대로 생성된 파일'이면 재생성/재호출을 하지 않기 위한 기준
    - product_no, product_url이 일치
    - CTA 문구/표(구분|상세) 중 하나라도 있으면 충분하다고 판단
    """
    fm = parse_front_matter(existing_md)
    if not fm:
        return False

    try:
        no_ok = int(fm.get("product_no", "-1")) == int(expected_no)
    except Exception:
        no_ok = False

    url_ok = (fm.get("product_url", "").strip() == expected_url.strip())

    if not (no_ok and url_ok):
        return False

    has_table = ("| 구분 | 상세 설명 |" in existing_md) or ("| --- | --- |" in existing_md)
    has_cta = ("놓치면 후회할 가격" in existing_md) or ("최저가 확인" in existing_md)

    return has_table or has_cta

def html_escape(s: str) -> str:
    return (
        str(s).replace("&", "&amp;")
              .replace("<", "&lt;")
              .replace(">", "&gt;")
              .replace('"', "&quot;")
    )

# ---------------------------------------
# GPT: intro + specs
# ---------------------------------------
def generate_intro_and_specs(name: str, desc: str) -> tuple[str, list[dict]]:
    if not name and not desc:
        return "", []

    system_msg = (
        "너는 한국 온라인 쇼핑몰 상세페이지를 요약해서 "
        "블로그/랜딩 페이지용 소개글을 만드는 마케터야.\n"
        "규칙:\n"
        "1) intro: 1~2문장, 80자 이내\n"
        "2) rows: 표 스펙 5~8개 (label/detail)\n"
        "3) JSON 한 줄:\n"
        "{"
        "\"intro\": \"...\", "
        "\"rows\": ["
        "{\"label\": \"소재\", \"detail\": \"...\"}"
        "]"
        "}"
    )

    user_msg = f"상품명: {name}\n간단 설명: {desc}\nJSON만 출력해줘."

    resp = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {"role": "system", "content": system_msg},
            {"role": "user", "content": user_msg},
        ],
        max_tokens=400,
    )

    text = resp.choices[0].message.content.strip()
    if text.startswith("```"):
        text = text.strip("`")
        lines = text.splitlines()
        if lines and "{" not in lines[0]:
            text = "\n".join(lines[1:])
        text = text.strip()

    try:
        data = json.loads(text)
    except Exception:
        return (desc or "").strip(), []

    intro = str(data.get("intro", "")).strip()
    rows = data.get("rows", []) or []

    cleaned = []
    for r in rows:
        try:
            label = str(r.get("label", "")).strip()
            detail = str(r.get("detail", "")).strip()
        except Exception:
            continue
        if label and detail:
            cleaned.append({"label": label, "detail": detail})

    return intro, cleaned

# ---------------------------------------
# 개별 상품 md
# ---------------------------------------
def build_markdown(
    no: int,
    name: str,
    short_title: str,
    product_url: str,
    image_url: str,
    intro: str,
    rows: list[dict],
    permalink: str,
) -> str:
    display_title = short_title or name
    heading = f"{no}번. {display_title}"

    lines: list[str] = []
    lines.append("---")
    lines.append(f'title: "{html_escape(display_title)}"')
    lines.append(f"product_no: {no}")
    lines.append(f'product_name: "{html_escape(name)}"')
    lines.append(f'product_url: "{product_url}"')
    lines.append(f'image_url: "{image_url}"')
    # ✅ GitHub Pages(Jekyll)에서 md 클릭 404 방지용 permalink
    lines.append(f'permalink: "{permalink}"')
    lines.append("---")
    lines.append("")

    lines.append(f"# {heading}")
    lines.append("")

    if image_url:
        lines.append(f"![{html_escape(display_title)}]({image_url})")
        lines.append("")

    if intro:
        lines.append(intro)
        lines.append("")

    if rows:
        lines.append("| 구분 | 상세 설명 |")
        lines.append("| --- | --- |")
        for r in rows:
            label = str(r["label"]).replace("|", "\\|")
            detail = str(r["detail"]).replace("|", "\\|")
            lines.append(f"| {label} | {detail} |")
        lines.append("")
    else:
        lines.append("상세 스펙은 판매 페이지에서 확인해 주세요.")
        lines.append("")

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

# ---------------------------------------
# index.md (카드형)
# ---------------------------------------
def build_index_markdown(items: list[dict]) -> str:
    lines: list[str] = []
    lines.append("---")
    lines.append('title: "하진팜 상품 모아보기"')
    lines.append("---")
    lines.append("")
    lines.append("# 하진팜 상품 모아보기")
    lines.append("")
    lines.append("인스타그램 프로필 링크에서 보신 **번호 그대로** 검색하신 뒤, 아래에서 상품을 선택해 보세요.")
    lines.append("")

    lines.append("<style>")
    lines.append("""
.product-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:18px;margin-top:18px}
.product-card{display:flex;flex-direction:column;padding:14px 16px;border-radius:16px;background:#fff;border:1px solid #e5e7eb;box-shadow:0 10px 25px rgba(15,23,42,.06);text-decoration:none;color:#111827;transition:transform .12s ease,box-shadow .12s ease,border-color .12s ease}
.product-card:hover{transform:translateY(-2px);border-color:#10b981;box-shadow:0 16px 35px rgba(16,185,129,.22)}
.product-badge{display:inline-flex;align-items:center;justify-content:center;font-size:11px;font-weight:700;color:#047857;background:#ecfdf5;border-radius:999px;padding:3px 9px;border:1px solid rgba(16,185,129,.5);margin-bottom:6px;max-width:fit-content}
.product-title{font-size:15px;font-weight:800;margin-bottom:6px;line-height:1.35}
.product-summary{font-size:13px;color:#4b5563;line-height:1.5;flex:1}
.product-cta{margin-top:10px;font-size:13px;font-weight:700;color:#059669}
.product-cta span{border-radius:999px;padding:6px 10px;background:#ecfdf5}
""")
    lines.append("</style>")
    lines.append("")

    lines.append('<div class="product-grid">')
    for it in sorted(items, key=lambda x: x["no"]):
        no = it["no"]
        title = html_escape(it["title"])
        summary = html_escape(it.get("summary", ""))
        # ✅ permalink 기반 링크로 변경 (가장 안전)
        href = it["permalink"]
        lines.append(f'<a class="product-card" href="{href}">')
        lines.append(f'  <div class="product-badge">{no}번</div>')
        lines.append(f'  <div class="product-title">{title}</div>')
        lines.append(f'  <div class="product-summary">{summary or "자세한 정보는 상세페이지에서 확인해 보세요."}</div>')
        lines.append('  <div class="product-cta"><span>자세히 보기 →</span></div>')
        lines.append("</a>")
    lines.append("</div>")
    lines.append("")
    return "\n".join(lines)

# ---------------------------------------
# 메인
# ---------------------------------------
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
        image_url = str(row.get("mainImage", "")).strip()
        short_title = str(row.get("shortTitle", "")).strip()
        base_desc = str(row.get("productDescription", "")).strip()

        if not name or not product_url:
            continue

        # ✅ 파일명 고정
        filename = f"product_{no:03d}.md"
        filepath = os.path.join(OUTPUT_DIR, filename)

        # ✅ permalink 고정 (폴더형 URL)
        permalink = f"/site_products/product_{no:03d}/"

        # ✅ 충분히 생성된 파일이면 스킵
        if os.path.exists(filepath):
            with open(filepath, "r", encoding="utf-8") as f:
                existing = f.read()

            if is_md_good_enough(existing, expected_no=no, expected_url=product_url):
                summary = (base_desc or "").strip()
                if len(summary) > 46:
                    summary = summary[:46].rstrip() + "…"

                index_items.append(
                    {"no": no, "title": short_title or name, "filename": filename, "summary": summary, "permalink": permalink}
                )
                print(f"[MD] 상품 {no}번 → 이미 존재(스킵): {filepath}")
                continue

        # 부족하거나 없으면 생성/업데이트
        intro, rows = generate_intro_and_specs(name, base_desc)

        md_content = build_markdown(
            no=no,
            name=name,
            short_title=short_title,
            product_url=product_url,
            image_url=image_url,
            intro=intro,
            rows=rows,
            permalink=permalink,
        )

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(md_content)

        summary_src = (intro or base_desc).strip()
        if len(summary_src) > 46:
            summary_src = summary_src[:46].rstrip() + "…"

        index_items.append(
            {"no": no, "title": short_title or name, "filename": filename, "summary": summary_src, "permalink": permalink}
        )

        print(f"[MD] 상품 {no}번 → 생성/업데이트 완료: {filepath}")

    # index.md는 매번 최신화
    index_md = build_index_markdown(index_items)
    index_path = os.path.join(OUTPUT_DIR, "index.md")
    with open(index_path, "w", encoding="utf-8") as f:
        f.write(index_md)

    print(f"[MD] 목차 페이지 생성 완료: {index_path}")

if __name__ == "__main__":
    main()