import os
import math
import json
import pandas as pd
from dotenv import load_dotenv
from openai import OpenAI

# -----------------------
# 환경변수 / 기본 설정
# -----------------------
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=OPENAI_API_KEY)

EXCEL_PATH = "products.xlsx"          # H:\hajinfam.github.io\products.xlsx
HTML_PATH = "insta/index.html"        # H:\hajinfam.github.io\insta\index.html

REQUIRED_COLUMNS = [
    "no",
    "productName",
    "productDescription",
    "mainImage",
    "link",
    "shortTitle",
]

# -----------------------
# GPT: shortTitle 생성
# -----------------------
def generate_short_title(product_name: str) -> str:
    if not product_name:
        return ""

    system_msg = (
        "너는 한국 온라인 쇼핑몰의 홍보 담당자야. "
        "인스타그램/랜딩페이지용 아주 짧은 제목을 만들어라. "
        "규칙:\n"
        "- 최대 12~15자\n"
        "- 브랜드명 제거\n"
        "- 핵심 기능 위주\n"
        "- 이모지, 마침표 금지"
    )

    user_msg = f"상품 이름: {product_name}\n한 줄 제목 생성:"

    resp = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {"role": "system", "content": system_msg},
            {"role": "user", "content": user_msg},
        ],
        max_tokens=50,
    )

    text = resp.choices[0].message.content.strip()
    return text.splitlines()[0].strip()

# -----------------------
# index.html products 교체
# -----------------------
def replace_products_in_html(products: list[dict]):
    with open(HTML_PATH, "r", encoding="utf-8") as f:
        html = f.read()

    start_tag = "// === AUTO_GENERATED_PRODUCTS_START ==="
    end_tag = "// === AUTO_GENERATED_PRODUCTS_END ==="

    if start_tag not in html or end_tag not in html:
        raise RuntimeError("index.html 에 자동 구간 태그가 없습니다.")

    start_idx = html.index(start_tag)
    end_idx = html.index(end_tag, start_idx)

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

    print(f"[DONE] insta/index.html 에 {len(products)}개의 상품이 반영되었습니다.")

# -----------------------
# 메인 처리
# -----------------------
def main():
    if not os.path.exists(EXCEL_PATH):
        raise FileNotFoundError(f"엑셀 없음: {EXCEL_PATH}")

    df = pd.read_excel(EXCEL_PATH)
    if df.empty:
        raise RuntimeError("엑셀에 데이터가 없습니다.")

    # 필요한 컬럼 자동 생성
    for col in REQUIRED_COLUMNS:
        if col not in df.columns:
            if col == "no":
                df[col] = list(range(1, len(df) + 1))
            else:
                df[col] = ""

    updated = False
    products: list[dict] = []

    for idx, row in df.iterrows():
        # 번호
        no = int(row["no"])
        # 전체 상품명
        name = str(row["productName"]).strip()

        # --- shortTitle 읽기 (NaN 처리 포함) ---
        raw_short = row.get("shortTitle", "")
        if pd.isna(raw_short):
            short_title = ""
        else:
            short_title = str(raw_short).strip()

        # 비어 있으면 GPT로 생성
        if not short_title:
            short_title = generate_short_title(name)
            df.at[idx, "shortTitle"] = short_title
            updated = True
            print(f"[GPT] {no}번 shortTitle => {short_title}")

        desc = str(row["productDescription"]).strip()
        link = str(row["link"]).strip()
        image_url = str(row["mainImage"]).strip()

        products.append(
            {
                "no": no,
                "title": f"{no}번. {short_title}",
                "description": desc,
                "link": link,
                "imageUrl": image_url,
            }
        )

    # GPT로 채운 shortTitle이 있으면 엑셀 저장
    if updated:
        df.to_excel(EXCEL_PATH, index=False)
        print("[INFO] products.xlsx 에 shortTitle 업데이트를 저장했습니다.")
    else:
        print("[INFO] 새로 채울 shortTitle 이 없어 엑셀 저장은 생략했습니다.")

    # 번호 정렬
    products.sort(key=lambda x: x["no"])

    # HTML 교체
    replace_products_in_html(products)


if __name__ == "__main__":
    main()
