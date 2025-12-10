import os
import json
import pandas as pd
from openai import OpenAI
from dotenv import load_dotenv

# -----------------------
# 환경변수 / 기본 설정
# -----------------------
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY 가 없습니다. .env 를 확인하세요.")

client = OpenAI(api_key=OPENAI_API_KEY)

EXCEL_PATH = "products.xlsx"
HTML_PATH = os.path.join("insta", "index.html")

REQUIRED_COLUMNS = [
    "no",
    "productName",
    "productDescription",
    "mainImage",
    "link",
    "shortTitle",
]


# -----------------------
# shortTitle GPT 생성
# -----------------------
def generate_short_title(product_name: str) -> str:
    """
    상품 전체 이름(productName)을 받아
    인스타/랜딩에서 쓸 짧은 제목(shortTitle)을 생성한다.
    """
    system_msg = (
        "너는 한국 온라인 쇼핑몰의 상품 홍보 담당자야. "
        "인스타그램용 '짧은 상품 제목'을 만들어야 한다. "
        "출력은 1줄, 16자 이내로 해라. "
        "말끝에 마침표, 느낌표 등은 붙이지 말고, 이모지도 넣지 마."
    )

    user_msg = (
        f"상품 전체 이름: {product_name}\n\n"
        "인스타그램과 랜딩페이지에서 사용할 짧은 제목을 한 줄로 만들어줘.\n"
        "예) '다용도 미끄럼방지 실내 겨울 방한 양말' → '다용도 방한양말'\n"
    )

    resp = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {"role": "system", "content": system_msg},
            {"role": "user", "content": user_msg},
        ],
        max_tokens=50,
    )

    text = resp.choices[0].message.content.strip()
    if not text:
        return product_name[:16]
    text = text.splitlines()[0].strip()
    return text


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

    start_idx = html.index(start_tag)
    end_idx = html.index(end_tag, start_idx)

    before = html[:start_idx]
    after = html[end_idx:]

    products_json = json.dumps(products, ensure_ascii=False, indent=2)

    middle = (
        f"{start_tag}\n"
        f"  const products = {products_json};\n"
        f"  {end_tag}"
    )

    new_html = before + middle + after

    with open(HTML_PATH, "w", encoding="utf-8") as f:
        f.write(new_html)

    print(f"[DONE] insta/index.html 에 {len(products)}개 상품을 반영했습니다.")


def main():
    # 1) 엑셀 읽기
    if not os.path.exists(EXCEL_PATH):
        raise FileNotFoundError(f"엑셀 파일을 찾을 수 없습니다: {EXCEL_PATH}")

    df = pd.read_excel(EXCEL_PATH)

    if df.empty:
        raise RuntimeError("products.xlsx 에 데이터가 없습니다.")

    # 필요한 컬럼이 없으면 만들어둠
    for col in REQUIRED_COLUMNS:
        if col not in df.columns:
            if col == "no":
                # 번호가 없으면 1부터 자동 부여
                df[col] = list(range(1, len(df) + 1))
            else:
                df[col] = ""

    # 2) shortTitle 비어 있는 행 → GPT로 생성
    updated_short_titles = False
    for idx, row in df.iterrows():
        name = str(row.get("productName", "")).strip()
        if not name:
            continue

        short = str(row.get("shortTitle", "")).strip()
        if not short:
            new_short = generate_short_title(name)
            df.at[idx, "shortTitle"] = new_short
            updated_short_titles = True
            print(f"[GPT] no={row.get('no')} → shortTitle = {new_short}")

    # 변경 사항이 있으면 엑셀 저장
    if updated_short_titles:
        df.to_excel(EXCEL_PATH, index=False)
        print("[INFO] products.xlsx 에 shortTitle 을 업데이트했습니다.")

    # 3) HTML에 넣을 products 리스트 생성
    products: list[dict] = []

    for _, row in df.iterrows():
        try:
            no = int(row.get("no"))
        except Exception:
            continue

        product_name = str(row.get("productName", "")).strip()
        link = str(row.get("link", "")).strip()
        if not product_name or not link:
            continue  # 필수 정보 없으면 스킵

        product = {
            "no": no,
            "shortTitle": str(row.get("shortTitle", "")).strip()
            or product_name[:16],
            "description": str(row.get("productDescription", "")).strip(),
            "url": link,
            "mainImage": str(row.get("mainImage", "")).strip(),
        }
        products.append(product)

    # 번호 순으로 정렬
    products.sort(key=lambda x: x["no"])

    # 4) index.html 의 products 배열 교체
    replace_products_in_html(products)


if __name__ == "__main__":
    main()