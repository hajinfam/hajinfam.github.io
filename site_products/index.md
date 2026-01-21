---
title: "HAJINFAM 할인상품 모아보기"
description: "인스타그램에서 소개된 상품을 번호로 빠르게 찾아볼 수 있는 모아보기 페이지입니다."
sitemap: true
noindex: false
---

# HAJINFAM 할인상품 모아보기

인스타그램에서 보신 **번호 그대로** 검색하거나, 아래 목록에서 상품을 선택해 보세요.

<style>

.product-grid{
  display:grid;
  grid-template-columns:repeat(auto-fit,minmax(230px,1fr));
  gap:18px;
  margin-top:18px
}
.product-card{
  display:flex;
  flex-direction:column;
  border-radius:16px;
  background:#fff;
  border:1px solid #e5e7eb;
  box-shadow:0 10px 25px rgba(15,23,42,.06);
  text-decoration:none;
  color:#111827;
  overflow:hidden;
  transition:transform .12s ease,box-shadow .12s ease,border-color .12s ease
}
.product-card:hover{
  transform:translateY(-2px);
  border-color:#10b981;
  box-shadow:0 16px 35px rgba(16,185,129,.22)
}
.product-thumb{
  position:relative;
  width:100%;
  aspect-ratio:16/9;
  background:#f3f4f6;
}
.product-thumb img{
  width:100%;
  height:100%;
  object-fit:cover;
  display:block
}
.product-badge{
  position:absolute;
  top:10px;
  left:10px;
  display:inline-flex;
  align-items:center;
  justify-content:center;
  font-size:12px;
  font-weight:800;
  line-height:1;
  color:#fff;
  padding:6px 10px;
  border-radius:999px;
  background:rgba(17,24,39,.55);
  border:1px solid rgba(255,255,255,.25);
  backdrop-filter:blur(4px)
}
.product-body{
  display:flex;
  flex-direction:column;
  gap:6px;
  padding:12px 14px 14px;
  min-height:120px;
}
.product-title{
  font-size:15px;
  font-weight:800;
  line-height:1.35;
  margin:0
}
.product-summary{
  font-size:13px;
  color:#4b5563;
  line-height:1.5;
  margin:0;
  flex:1;
  display:-webkit-box;
  -webkit-line-clamp:2;
  -webkit-box-orient:vertical;
  overflow:hidden
}
.product-cta{
  margin-top:6px;
  font-size:13px;
  font-weight:700;
  color:#059669
}
.product-cta span{
  border-radius:999px;
  padding:6px 10px;
  background:#ecfdf5;
  display:inline-block
}

</style>

<div class="product-grid">
</div>
