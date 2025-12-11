import os
import math
import json
import pandas as pd
from dotenv import load_dotenv
from openai import OpenAI

# -----------------------
# 환경 변수 / 기본 설정
# -----------------------
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY 가 설정되어 있지 않습니다. .env 를 확인하세요.")

client = OpenAI(api_key=OPENAI_API_KEY)

EXCEL_PATH = "products.xlsx"          # 엑셀 파일
HTML_PATH  = "insta/index.html"       # 랜딩 페이지 html

# 엑셀 / 구글시트에 있어야 하는 컬럼들
REQUIRED_COLUMNS = [
    "no",
    "productName",
    "productUrl",          # 🔹 link 대신 productUrl 사용
    "mainImage",
    "shortTitle",
    "productDescription",
]

# -----------------------
# GPT: shortTitle + productDescription 동시 생성
# -----------------------
def generate_short_title_and_desc(product_name: str) -> tuple[str, str]:
    """
    전체 상품명(productName)을 받아
    - shortTitle (최대 12~15자)
    - productDescription (40~80자 정도 한두 문장)
    을 한 번에 생성
    """
    if not product_name:
        return "", ""

    system_msg = (
        "너는 한국 온라인 쇼핑몰의 감성 마케팅 카피라이터야.\n"
        "각 상품에 대해 다음 두 가지를 만들어라.\n"
        "1) shortTitle: 최대 12~15자, 브랜드명 제외, 핵심 효능/용도 중심, 이모지/마침표 없음.\n"
        "2) productDescription: 40~80자, 1~2문장, 고객의 고민을 공감하며 구매를 유도.\n"
        "출력 형식은 반드시 JSON 한 줄로만:\n"
        "{\"shortTitle\": \"...\", \"productDescription\": \"...\"}"
    )

    user_msg = f"상품명: {product_name}\n해당 규칙에 맞게 JSON 한 줄만 출력해줘."

    resp = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {"role": "system", "content": system_msg},
            {"role": "user", "content": user_msg},
        ],
        max_tokens=200,
    )

    text = resp.choices[0].message.content.strip()

    # ```json ... ``` 로 나오는 경우 처리
    if text.startswith("```"):
        text = text.strip("`")
        lines = text.splitlines()
        # 첫 줄에 ```json 같은 게 있으면 제거
        if lines and "{" not in lines[0]:
            text = "\n".join(lines[1:])
    text = text.strip()

    try:
        # 작은따옴표로 올 경우까지 대비해서 치환 후 파싱
        data = json.loads(text.replace("'", "\""))
    except Exception:
        # 파싱 실패 시 최소한의 fallback
        return product_name[:15], ""

    short_title = str(data.get("shortTitle", "")).strip()
    desc = str(data.get("productDescription", "")).strip()

    if not short_title:
        short_title = product_name[:15]

    return short_title, desc


# -----------------------
# HTML 안 products 배열 교체
# -----------------------
def replace_products_in_html(products: list[dict]):
    with open(HTML_PATH, "r", encoding="utf-8") as f:
        html = f.read()

    start_tag = "// === AUTO_GENERATED_PRODUCTS_START ==="
    end_tag = "// === AUTO_GENERATED_PRODUCTS_END ==="

    if start_tag not in html or end_tag not in html:
        raise RuntimeError("index.html 에 자동 구간 태그를 찾을 수 없습니다.")

    # start_tag 위치부터 end_tag 끝까지를 통째로 교체
    start_idx = html.index(start_tag)
    end_idx = html.index(end_tag, start_idx) + len(end_tag)

    before = html[:start_idx]
    after = html[end_idx:]

    products_json = json.dumps(products, ensure_ascii=False, indent=2)

    middle = (
        f"{start_tag}\n"
        f"  const products = {products_json};\n"
        f"{end_tag}"
    )

    new_html = before + middle + after

    with open(HTML_PATH, "w", encoding="utf-8") as f:
        f.write(new_html)

    print(f"[DONE] insta/index.html 에 {len(products)}개의 상품을 반영했습니다.")


# -----------------------
# 메인 로직
# -----------------------
def main():
    # 1) 엑셀 읽기
    if not os.path.exists(EXCEL_PATH):
        raise FileNotFoundError(f"엑셀 파일을 찾을 수 없습니다: {EXCEL_PATH}")

    df = pd.read_excel(EXCEL_PATH)

    if df.empty:
        raise RuntimeError("products.xlsx 에 데이터가 없습니다.")

    # 필요한 컬럼이 없으면 생성
    for col in REQUIRED_COLUMNS:
        if col not in df.columns:
            if col == "no":
                # 번호가 없으면 1부터 자동 부여
                df[col] = list(range(1, len(df) + 1))
            else:
                df[col] = ""

    # 2) 비어 있는 shortTitle / productDescription을 GPT로 채우기
    updated = False
    for idx, row in df.iterrows():
        name = str(row.get("productName", "")).strip()
        if not name:
            continue

        st_raw = row.get("shortTitle", "")
        if isinstance(st_raw, float) and math.isnan(st_raw):
            st_raw = ""
        short_title = str(st_raw).strip()

        desc_raw = row.get("productDescription", "")
        if isinstance(desc_raw, float) and math.isnan(desc_raw):
            desc_raw = ""
        desc = str(desc_raw).strip()

        # 둘 중 하나라도 비어 있으면 GPT 호출
        if not short_title or not desc:
            new_short, new_desc = generate_short_title_and_desc(name)
            if new_short:
                df.at[idx, "shortTitle"] = new_short
            if new_desc:
                df.at[idx, "productDescription"] = new_desc
            updated = True
            print(
                f"[GPT] no={row.get('no')} → "
                f"shortTitle='{new_short}', desc='{new_desc[:25]}…'"
            )

    # 변경사항이 있으면 엑셀 저장
    if updated:
        df.to_excel(EXCEL_PATH, index=False)
        print("[INFO] products.xlsx 에 shortTitle / productDescription 을 업데이트했습니다.")

    # 3) HTML에 넣을 products 리스트 생성
    products: list[dict] = []

    for idx, row in df.iterrows():
        no_val = row.get("no")
        try:
            no = int(no_val)
        except Exception:
            continue

        name = str(row.get("productName", "")).strip()

        st = str(row.get("shortTitle", "")).strip()

        desc_val = row.get("productDescription", "")
        if isinstance(desc_val, float) and math.isnan(desc_val):
            desc_val = ""
        desc = str(desc_val).strip()

        url_val = row.get("productUrl", "")
        if isinstance(url_val, float) and math.isnan(url_val):
            url_val = ""
        product_url = str(url_val).strip()

        img_val = row.get("mainImage", "")
        if isinstance(img_val, float) and math.isnan(img_val):
            img_val = ""
        image_url = str(img_val).strip()

        # 필수 정보 없으면 건너뜀 (상품명 / URL)
        if not name or not product_url:
            continue

        # 카드에 보이는 제목: "1번. 쇼트타이틀"
        title_text = f"{no}번. {st if st else name[:15]}"

        products.append(
            {
                "no": no,
                "title": title_text,   # 화면에 굵게 보이는 제목
                "description": desc,   # 한두 줄 설명
                "link": product_url,   # 네이버 스토어 링크 (프론트에서는 key 이름을 link 로 사용)
                "imageUrl": image_url, # 썸네일 이미지
            }
        )

    # 번호 순 정렬
    products.sort(key=lambda x: x["no"])

    # 4) index.html 의 products 배열 교체
    replace_products_in_html(products)


if __name__ == "__main__":
    main()