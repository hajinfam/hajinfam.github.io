---
title: "하진팜 상품 모아보기"
description: "인스타그램에서 소개된 상품을 번호로 빠르게 찾아볼 수 있는 모아보기 페이지입니다."
sitemap: true
noindex: false
---

# 하진팜 상품 모아보기

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
  overflow:hidden; /* 이미지/배지 카드 밖 방지 */
  transition:transform .12s ease,box-shadow .12s ease,border-color .12s ease
}

.product-card:hover{
  transform:translateY(-2px);
  border-color:#10b981;
  box-shadow:0 16px 35px rgba(16,185,129,.22)
}

/* 상단 썸네일 영역 */
.product-thumb{
  position:relative;
  width:100%;
  aspect-ratio:16/9;    /* 카드 전체 크기 느낌 유지 */
  background:#f3f4f6;   /* 이미지 없을 때 대비 */
}

.product-thumb img{
  width:100%;
  height:100%;
  object-fit:cover;
  display:block
}

/* 번호를 사진 안으로 */
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

/* 본문(기존 카드 패딩은 여기로 이동) */
.product-body{
  display:flex;
  flex-direction:column;
  gap:6px;
  padding:12px 14px 14px;
  min-height:120px; /* 텍스트 길이 차로 카드 높이 흔들림 완화 */
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
  -webkit-line-clamp:2;            /* 2줄 고정으로 높이 안정 */
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
<a class="product-card" href="/site_products/product_001/">
  <div class="product-thumb">
    <img src="https://shop-phinf.pstatic.net/20221031_127/1667199162521wbDVQ_JPEG/68335061228336326_657608575.jpg" alt="45cm 미니 크리스마스 트리" loading="lazy" />
    <div class="product-badge">1번</div>
  </div>
  <div class="product-body">
    <h3 class="product-title">45cm 미니 크리스마스 트리</h3>
    <p class="product-summary">작은 공간을 화사하게 꾸며주는 45cm 미니 크리스마스트리 풀세트로, 전구 포함해…</p>
    <div class="product-cta"><span>자세히 보기 →</span></div>
  </div>
</a>
<a class="product-card" href="/site_products/product_002/">
  <div class="product-thumb">
    <img src="https://shop-phinf.pstatic.net/20241120_247/1732090908328AggYN_JPEG/568915876437276_1930833792.jpg" alt="미니 크리스마스트리 전구 세트" loading="lazy" />
    <div class="product-badge">2번</div>
  </div>
  <div class="product-body">
    <h3 class="product-title">미니 크리스마스트리 전구 세트</h3>
    <p class="product-summary">작은 공간에 딱 맞는 60cm 미니 크리스마스트리와 전구 세트로 따뜻한 연말 분위기…</p>
    <div class="product-cta"><span>자세히 보기 →</span></div>
  </div>
</a>
<a class="product-card" href="/site_products/product_003/">
  <div class="product-thumb">
    <img src="https://shop-phinf.pstatic.net/20250926_28/1758871462021fy9WH_JPEG/9234680545723543_992110204.jpg" alt="150cm 전구일체형 전나무 트리" loading="lazy" />
    <div class="product-badge">3번</div>
  </div>
  <div class="product-body">
    <h3 class="product-title">150cm 전구일체형 전나무 트리</h3>
    <p class="product-summary">전구가 일체형으로 설치가 편리한 150cm 전나무 크리스마스트리로 집안을 따뜻하고…</p>
    <div class="product-cta"><span>자세히 보기 →</span></div>
  </div>
</a>
<a class="product-card" href="/site_products/product_004/">
  <div class="product-thumb">
    <img src="https://shop-phinf.pstatic.net/20251110_233/1762753004020JnvvV_JPEG/45185075123977079_605772484.jpg" alt="크리스마스 오르골 무드등" loading="lazy" />
    <div class="product-badge">4번</div>
  </div>
  <div class="product-body">
    <h3 class="product-title">크리스마스 오르골 무드등</h3>
    <p class="product-summary">따뜻한 조명과 멜로디가 어우러진 크리스마스 스노우볼로 연말 분위기를 더욱 특별하게…</p>
    <div class="product-cta"><span>자세히 보기 →</span></div>
  </div>
</a>
<a class="product-card" href="/site_products/product_005/">
  <div class="product-thumb">
    <img src="https://shop-phinf.pstatic.net/20250905_228/1757038877436WuX2m_JPEG/40849809432601330_1125731568.jpg" alt="대형 크리스마스 가랜드" loading="lazy" />
    <div class="product-badge">5번</div>
  </div>
  <div class="product-body">
    <h3 class="product-title">대형 크리스마스 가랜드</h3>
    <p class="product-summary">풍성한 그린 전나무 가랜드로 현관과 벽을 화사하게 꾸미기에 적합한 크리스마스 장식입…</p>
    <div class="product-cta"><span>자세히 보기 →</span></div>
  </div>
</a>
<a class="product-card" href="/site_products/product_006/">
  <div class="product-thumb">
    <img src="https://shop-phinf.pstatic.net/20221101_78/1667285988930nBDR6_JPEG/68421822725526886_379458607.jpg" alt="LED 야광 고양이 머리띠" loading="lazy" />
    <div class="product-badge">6번</div>
  </div>
  <div class="product-body">
    <h3 class="product-title">LED 야광 고양이 머리띠</h3>
    <p class="product-summary">LED 빛나는 고양이 머리띠로 생일, 할로윈, 크리스마스 파티를 더욱 특별하게 연출…</p>
    <div class="product-cta"><span>자세히 보기 →</span></div>
  </div>
</a>
<a class="product-card" href="/site_products/product_007/">
  <div class="product-thumb">
    <img src="https://shop-phinf.pstatic.net/20251111_297/1762827045499vAUQa_JPEG/17525346596007412_1805044427.jpg" alt="움직이는 기차 오르골" loading="lazy" />
    <div class="product-badge">7번</div>
  </div>
  <div class="product-body">
    <h3 class="product-title">움직이는 기차 오르골</h3>
    <p class="product-summary">감성 가득한 움직이는 기차 오르골로 따뜻한 크리스마스 분위기를 연출하며 특별한 선물…</p>
    <div class="product-cta"><span>자세히 보기 →</span></div>
  </div>
</a>
<a class="product-card" href="/site_products/product_008/">
  <div class="product-thumb">
    <img src="https://shop-phinf.pstatic.net/20240927_22/17274228566063Nu4n_JPEG/61555714704941476_342412971.jpg" alt="포근한 양모 트리 스커트" loading="lazy" />
    <div class="product-badge">8번</div>
  </div>
  <div class="product-body">
    <h3 class="product-title">포근한 양모 트리 스커트</h3>
    <p class="product-summary">포근한 양모 소재로 겨울철 크리스마스 트리에 따뜻함을 더하는 60cm 스커트입니다.…</p>
    <div class="product-cta"><span>자세히 보기 →</span></div>
  </div>
</a>
<a class="product-card" href="/site_products/product_009/">
  <div class="product-thumb">
    <img src="https://shop-phinf.pstatic.net/20241213_8/17340703644297BxWp_JPEG/17881205318910450_409354498.jpg" alt="무선 안드로이드 오토 동글" loading="lazy" />
    <div class="product-badge">9번</div>
  </div>
  <div class="product-body">
    <h3 class="product-title">무선 안드로이드 오토 동글</h3>
    <p class="product-summary">무선으로 안드로이드 오토를 간편하게 연결해주는 카플 AAWireless 2 동글로…</p>
    <div class="product-cta"><span>자세히 보기 →</span></div>
  </div>
</a>
<a class="product-card" href="/site_products/product_010/">
  <div class="product-thumb">
    <img src="https://shop-phinf.pstatic.net/20250905_186/1757064393149bD6th_JPEG/90817591629460387_2040145490.jpg" alt="심박수 측정 스마트 밴드" loading="lazy" />
    <div class="product-badge">10번</div>
  </div>
  <div class="product-body">
    <h3 class="product-title">심박수 측정 스마트 밴드</h3>
    <p class="product-summary">정확한 심박수 측정과 만보기 기능으로 운동과 러닝 시 건강 관리를 돕는 스마트 워치…</p>
    <div class="product-cta"><span>자세히 보기 →</span></div>
  </div>
</a>
<a class="product-card" href="/site_products/product_011/">
  <div class="product-thumb">
    <img src="https://shop-phinf.pstatic.net/20241202_29/17331027876933cNNl_JPEG/19868530163881398_1602592050.jpg" alt="정확한 위치 추적기" loading="lazy" />
    <div class="product-badge">11번</div>
  </div>
  <div class="product-body">
    <h3 class="product-title">정확한 위치 추적기</h3>
    <p class="product-summary">아이와 귀중품을 안전하게 지키는 삼성 갤럭시 스마트 태그2, 원격 위치추적과 UWB…</p>
    <div class="product-cta"><span>자세히 보기 →</span></div>
  </div>
</a>
<a class="product-card" href="/site_products/product_012/">
  <div class="product-thumb">
    <img src="https://shop-phinf.pstatic.net/20250228_131/17407235862945oMRT_JPEG/87097046226135825_1266053080.jpg" alt="블루투스 셀카 삼각대" loading="lazy" />
    <div class="product-badge">12번</div>
  </div>
  <div class="product-body">
    <h3 class="product-title">블루투스 셀카 삼각대</h3>
    <p class="product-summary">흔들림 없는 완벽한 셀카 촬영을 위한 올인원 삼각대 블루투스 셀카봉으로 스마트한 촬…</p>
    <div class="product-cta"><span>자세히 보기 →</span></div>
  </div>
</a>
<a class="product-card" href="/site_products/product_013/">
  <div class="product-thumb">
    <img src="https://shop-phinf.pstatic.net/20250908_43/1757298331836lMKkK_JPEG/91306051896156888_898425836.jpg" alt="운동 최적화 스마트 워치" loading="lazy" />
    <div class="product-badge">13번</div>
  </div>
  <div class="product-body">
    <h3 class="product-title">운동 최적화 스마트 워치</h3>
    <p class="product-summary">러닝과 운동 중 실시간 활동 데이터를 기록해 목표 달성을 지원하는 샤오미 레드미 워…</p>
    <div class="product-cta"><span>자세히 보기 →</span></div>
  </div>
</a>
<a class="product-card" href="/site_products/product_014/">
  <div class="product-thumb">
    <img src="https://shop-phinf.pstatic.net/20240927_39/1727400379472DQTUT_JPEG/15699937494177277_361597048.jpg" alt="고성능 LTE 태블릿PC" loading="lazy" />
    <div class="product-badge">14번</div>
  </div>
  <div class="product-body">
    <h3 class="product-title">고성능 LTE 태블릿PC</h3>
    <p class="product-summary">빠르고 넉넉한 저장공간을 갖춘 아이뮤즈 뮤패드 K11 LTE는 일상과 업무용 태블릿…</p>
    <div class="product-cta"><span>자세히 보기 →</span></div>
  </div>
</a>
<a class="product-card" href="/site_products/product_015/">
  <div class="product-thumb">
    <img src="https://shop-phinf.pstatic.net/20240819_68/1724027723542VVf1H_JPEG/51365116327154854_1852510496.jpg" alt="차량용 포레스트 방향제 80ml" loading="lazy" />
    <div class="product-badge">15번</div>
  </div>
  <div class="product-body">
    <h3 class="product-title">차량용 포레스트 방향제 80ml</h3>
    <p class="product-summary">차량 내 답답한 냄새를 상쾌한 포레스트가든 향기로 채워주며 1+1 구성으로 경제적인…</p>
    <div class="product-cta"><span>자세히 보기 →</span></div>
  </div>
</a>
<a class="product-card" href="/site_products/product_016/">
  <div class="product-thumb">
    <img src="https://shop-phinf.pstatic.net/20230925_287/1695632594321Cmm6C_JPEG/15567567921752873_555173247.jpg" alt="두꺼운 우풍차단 비닐" loading="lazy" />
    <div class="product-badge">16번</div>
  </div>
  <div class="product-body">
    <h3 class="product-title">두꺼운 우풍차단 비닐</h3>
    <p class="product-summary">두꺼운 대형 비닐 커튼으로 창문과 현관 틈새 바람을 효과적으로 차단해 추위로부터 실…</p>
    <div class="product-cta"><span>자세히 보기 →</span></div>
  </div>
</a>
<a class="product-card" href="/site_products/product_017/">
  <div class="product-thumb">
    <img src="https://shop-phinf.pstatic.net/20240708_107/1720410690591NRdag_JPEG/1103900859598527_1402585696.jpg" alt="아기용 회전 비데 수전" loading="lazy" />
    <div class="product-badge">17번</div>
  </div>
  <div class="product-body">
    <h3 class="product-title">아기용 회전 비데 수전</h3>
    <p class="product-summary">신생아 피부에 부드러운 세정과 편리한 회전 기능을 갖춘 아기 비데 워터탭, 필터 3…</p>
    <div class="product-cta"><span>자세히 보기 →</span></div>
  </div>
</a>
<a class="product-card" href="/site_products/product_018/">
  <div class="product-thumb">
    <img src="https://shop-phinf.pstatic.net/20230925_287/1695632594321Cmm6C_JPEG/15567567921752873_555173247.jpg" alt="대형 방풍 우풍차단 비닐" loading="lazy" />
    <div class="product-badge">18번</div>
  </div>
  <div class="product-body">
    <h3 class="product-title">대형 방풍 우풍차단 비닐</h3>
    <p class="product-summary">두꺼운 맞춤 비닐로 겨울철 우풍과 소음을 효과적으로 차단하여 실내 온도를 유지하는…</p>
    <div class="product-cta"><span>자세히 보기 →</span></div>
  </div>
</a>
<a class="product-card" href="/site_products/product_019/">
  <div class="product-thumb">
    <img src="https://shop-phinf.pstatic.net/20251023_115/1761211850133FRxx9_PNG/15387102926594746_1605516923.png" alt="벽걸이 욕실 온풍기" loading="lazy" />
    <div class="product-badge">19번</div>
  </div>
  <div class="product-body">
    <h3 class="product-title">벽걸이 욕실 온풍기</h3>
    <p class="product-summary">추운 욕실에서 빠르게 따뜻함을 제공하는 벽걸이형 온풍기로 공간 활용이 뛰어나며 안전…</p>
    <div class="product-cta"><span>자세히 보기 →</span></div>
  </div>
</a>
<a class="product-card" href="/site_products/product_020/">
  <div class="product-thumb">
    <img src="https://shop-phinf.pstatic.net/20250924_28/1758676576537EYoku_JPEG/6546070264973758_920198057.jpg" alt="신생아용 가열식 가습기" loading="lazy" />
    <div class="product-badge">20번</div>
  </div>
  <div class="product-body">
    <h3 class="product-title">신생아용 가열식 가습기</h3>
    <p class="product-summary">신생아 방에 적합한 에어메이드 가열식 가습기로 건강한 습도 조절과 자동 세척 기능을…</p>
    <div class="product-cta"><span>자세히 보기 →</span></div>
  </div>
</a>
<a class="product-card" href="/site_products/product_021/">
  <div class="product-thumb">
    <img src="https://shop-phinf.pstatic.net/20251107_236/1762499531292mAaJn_JPEG/35033975560962307_906682600.jpeg" alt="보풀 제거 전문 니트 세탁기" loading="lazy" />
    <div class="product-badge">21번</div>
  </div>
  <div class="product-body">
    <h3 class="product-title">보풀 제거 전문 니트 세탁기</h3>
    <p class="product-summary">니트 보풀 걱정 없이 깔끔한 의류 관리가 가능한 프리미엄 보풀 제거기입니다. 세탁소…</p>
    <div class="product-cta"><span>자세히 보기 →</span></div>
  </div>
</a>
<a class="product-card" href="/site_products/product_022/">
  <div class="product-thumb">
    <img src="https://shop-phinf.pstatic.net/20250123_218/1737609793942smSh5_JPEG/73945063421327_269656625.jpg" alt="저온 완벽살균 대용량 가습기" loading="lazy" />
    <div class="product-badge">22번</div>
  </div>
  <div class="product-body">
    <h3 class="product-title">저온 완벽살균 대용량 가습기</h3>
    <p class="product-summary">저온 가열로 완벽 살균되어 위생적인 대용량 가습기로 건조한 실내 공기를 촉촉하게 유…</p>
    <div class="product-cta"><span>자세히 보기 →</span></div>
  </div>
</a>
<a class="product-card" href="/site_products/product_023/">
  <div class="product-thumb">
    <img src="https://shop-phinf.pstatic.net/20250627_293/1751006736835cb2VB_JPEG/5579795974650774_1714364793.jpg" alt="노이즈캔슬링 오픈형 이어폰" loading="lazy" />
    <div class="product-badge">23번</div>
  </div>
  <div class="product-body">
    <h3 class="product-title">노이즈캔슬링 오픈형 이어폰</h3>
    <p class="product-summary">ENC 노이즈캔슬링 기술로 소음 걱정 없이 선명한 음악 감상, 오픈형 블루투스 이어…</p>
    <div class="product-cta"><span>자세히 보기 →</span></div>
  </div>
</a>
<a class="product-card" href="/site_products/product_024/">
  <div class="product-thumb">
    <img src="https://shop-phinf.pstatic.net/20251021_61/1761008802600sm4Cz_JPEG/95141641731442454_589146379.jpg" alt="탁상용 초음파 가습기" loading="lazy" />
    <div class="product-badge">24번</div>
  </div>
  <div class="product-body">
    <h3 class="product-title">탁상용 초음파 가습기</h3>
    <p class="product-summary">조용하고 작은 초음파 가습기로 사무실 공기 건조함을 효과적으로 개선하며, 간편한 세…</p>
    <div class="product-cta"><span>자세히 보기 →</span></div>
  </div>
</a>
<a class="product-card" href="/site_products/product_025/">
  <div class="product-thumb">
    <img src="https://shop-phinf.pstatic.net/20241118_171/1731895960486HOpWb_JPEG/323422604722331_495017488.jpg" alt="포근한 난방 패브릭 텐트" loading="lazy" />
    <div class="product-badge">25번</div>
  </div>
  <div class="product-body">
    <h3 class="product-title">포근한 난방 패브릭 텐트</h3>
    <p class="product-summary">추운 겨울에도 따뜻하게 사용하는 난방 텐트로 쾌적한 수면 공간을 만들어 줍니다. 슈…</p>
    <div class="product-cta"><span>자세히 보기 →</span></div>
  </div>
</a>
<a class="product-card" href="/site_products/product_026/">
  <div class="product-thumb">
    <img src="https://shop-phinf.pstatic.net/20240925_43/1727247121467EsFej_JPEG/61379945672017850_902973394.jpg" alt="포근한 실내 난방 텐트" loading="lazy" />
    <div class="product-badge">26번</div>
  </div>
  <div class="product-body">
    <h3 class="product-title">포근한 실내 난방 텐트</h3>
    <p class="product-summary">추운 겨울에도 따뜻하고 포근한 수면 환경을 제공하는 보온 난방 텐트로 실내 사용에…</p>
    <div class="product-cta"><span>자세히 보기 →</span></div>
  </div>
</a>
<a class="product-card" href="/site_products/product_027/">
  <div class="product-thumb">
    <img src="https://shop-phinf.pstatic.net/20251125_58/1764060075073JQf9t_JPEG/18587057830696921_1446136759.jpg" alt="포근한 겨울 방한 슬리퍼" loading="lazy" />
    <div class="product-badge">27번</div>
  </div>
  <div class="product-body">
    <h3 class="product-title">포근한 겨울 방한 슬리퍼</h3>
    <p class="product-summary">따뜻한 플리스와 패딩으로 겨울철 발을 포근하게 보호하는 나이키 버로우 털 슬리퍼입니…</p>
    <div class="product-cta"><span>자세히 보기 →</span></div>
  </div>
</a>
<a class="product-card" href="/site_products/product_028/">
  <div class="product-thumb">
    <img src="https://shop-phinf.pstatic.net/20250305_129/1741140926671AmyOJ_JPEG/75273732410163524_139688753.jpg" alt="따뜻한 보아털 후드 집업" loading="lazy" />
    <div class="product-badge">28번</div>
  </div>
  <div class="product-body">
    <h3 class="product-title">따뜻한 보아털 후드 집업</h3>
    <p class="product-summary">추운 겨울 야외에서도 따뜻한 보아털 후드집업, 빅사이즈로 편안한 착용감을 제공합니다…</p>
    <div class="product-cta"><span>자세히 보기 →</span></div>
  </div>
</a>
<a class="product-card" href="/site_products/product_029/">
  <div class="product-thumb">
    <img src="https://shop-phinf.pstatic.net/20241222_133/17348056359229qYSC_JPEG/70852511689562404_401854286.jpg" alt="포근한 양털 겨울 귀도리" loading="lazy" />
    <div class="product-badge">29번</div>
  </div>
  <div class="product-body">
    <h3 class="product-title">포근한 양털 겨울 귀도리</h3>
    <p class="product-summary">부드러운 양털 소재로 제작된 방한 이어머프로 겨울철 차가운 바람으로부터 귀를 따뜻하…</p>
    <div class="product-cta"><span>자세히 보기 →</span></div>
  </div>
</a>
<a class="product-card" href="/site_products/product_030/">
  <div class="product-thumb">
    <img src="https://shop-phinf.pstatic.net/20251118_192/1763454741284rRVOV_PNG/60932875818579484_1409168096.png" alt="스마트폰 터치 방한장갑" loading="lazy" />
    <div class="product-badge">30번</div>
  </div>
  <div class="product-body">
    <h3 class="product-title">스마트폰 터치 방한장갑</h3>
    <p class="product-summary">추운 겨울에도 손 시림 없이 스마트폰 터치가 가능하며, 부드러운 기모로 따뜻한 착용…</p>
    <div class="product-cta"><span>자세히 보기 →</span></div>
  </div>
</a>
<a class="product-card" href="/site_products/product_031/">
  <div class="product-thumb">
    <img src="https://shop-phinf.pstatic.net/20251031_18/17618851287512l7Wq_JPEG/87516762761071598_1836635782.jpg" alt="가벼운 경량 방한 목도리" loading="lazy" />
    <div class="product-badge">31번</div>
  </div>
  <div class="product-body">
    <h3 class="product-title">가벼운 경량 방한 목도리</h3>
    <p class="product-summary">가벼우면서도 따뜻한 경량 패딩 목도리로 겨울철 추위를 효과적으로 막아줍니다. 야외활…</p>
    <div class="product-cta"><span>자세히 보기 →</span></div>
  </div>
</a>
<a class="product-card" href="/site_products/product_032/">
  <div class="product-thumb">
    <img src="https://shop-phinf.pstatic.net/20250822_196/1755829583922m2i9q_JPEG/7599366041362571_1796467425.jpg" alt="간편 변기 세정 스틱" loading="lazy" />
    <div class="product-badge">32번</div>
  </div>
  <div class="product-body">
    <h3 class="product-title">간편 변기 세정 스틱</h3>
    <p class="product-summary">New 닥터퓨리 변기세정제 스틱과 청소포 12개입으로 번거로운 변기 청소를 간편하게…</p>
    <div class="product-cta"><span>자세히 보기 →</span></div>
  </div>
</a>
<a class="product-card" href="/site_products/product_033/">
  <div class="product-thumb">
    <img src="https://shop-phinf.pstatic.net/20250118_39/1737189262496Akyes_JPEG/71322074642706286_584694950.jpg" alt="황금 소원 거북이 부적" loading="lazy" />
    <div class="product-badge">33번</div>
  </div>
  <div class="product-body">
    <h3 class="product-title">황금 소원 거북이 부적</h3>
    <p class="product-summary">개업, 승진, 재물, 합격 등 다양한 소원에 맞춘 황금 소원 거북이 부적으로 행운을…</p>
    <div class="product-cta"><span>자세히 보기 →</span></div>
  </div>
</a>
<a class="product-card" href="/site_products/product_034/">
  <div class="product-thumb">
    <img src="https://shop-phinf.pstatic.net/20241025_235/1729821965410is2tP_JPEG/6309273534817397_718649002.jpg" alt="2025년 짱구 벽걸이 달력" loading="lazy" />
    <div class="product-badge">34번</div>
  </div>
  <div class="product-body">
    <h3 class="product-title">2025년 짱구 벽걸이 달력</h3>
    <p class="product-summary">귀여운 짱구 캐릭터가 돋보이는 2025년 벽걸이 달력으로 새해 일정을 쉽게 관리하고…</p>
    <div class="product-cta"><span>자세히 보기 →</span></div>
  </div>
</a>
<a class="product-card" href="/site_products/product_035/">
  <div class="product-thumb">
    <img src="https://shop-phinf.pstatic.net/20251117_226/17633852195067Mw1T_JPEG/18065954483823832_2026591829.jpg" alt="작은 복주머니 선물용" loading="lazy" />
    <div class="product-badge">35번</div>
  </div>
  <div class="product-body">
    <h3 class="product-title">작은 복주머니 선물용</h3>
    <p class="product-summary">전통 복조리 디자인의 미니 복주머니로 새해 행운을 전하고 외국인 선물로도 좋은 명절…</p>
    <div class="product-cta"><span>자세히 보기 →</span></div>
  </div>
</a>
<a class="product-card" href="/site_products/product_036/">
  <div class="product-thumb">
    <img src="https://shop-phinf.pstatic.net/20230602_147/1685682054414QwpOL_JPEG/31425722217311814_1865601803.jpg" alt="미니 크리스마스 감사카드" loading="lazy" />
    <div class="product-badge">36번</div>
  </div>
  <div class="product-body">
    <h3 class="product-title">미니 크리스마스 감사카드</h3>
    <p class="product-summary">소중한 마음을 전하는 미니 크리스마스카드로 새해 인사와 감사를 전하기에 적합한 8c…</p>
    <div class="product-cta"><span>자세히 보기 →</span></div>
  </div>
</a>
<a class="product-card" href="/site_products/product_037/">
  <div class="product-thumb">
    <img src="https://shop-phinf.pstatic.net/20250924_270/1758705738235S33tL_JPEG/8796685156155698_856278412.jpg" alt="황금빗자루 액막이 선물" loading="lazy" />
    <div class="product-badge">37번</div>
  </div>
  <div class="product-body">
    <h3 class="product-title">황금빗자루 액막이 선물</h3>
    <p class="product-summary">액막이와 행운을 담는 황금빗자루로 신혼집들이, 개업, 이사 선물로 적합한 맞춤 각인…</p>
    <div class="product-cta"><span>자세히 보기 →</span></div>
  </div>
</a>
<a class="product-card" href="/site_products/product_038/">
  <div class="product-thumb">
    <img src="https://shop-phinf.pstatic.net/20251207_17/1765062713833zPYpN_JPEG/745897979639105_606870278.jpg" alt="2024 신년 행운 푸른 용 키링" loading="lazy" />
    <div class="product-badge">38번</div>
  </div>
  <div class="product-body">
    <h3 class="product-title">2024 신년 행운 푸른 용 키링</h3>
    <p class="product-summary">2024년 용의 해를 기념하는 맞춤 용띠 키링으로 새해 행운과 특별한 기운을 더하세…</p>
    <div class="product-cta"><span>자세히 보기 →</span></div>
  </div>
</a>
<a class="product-card" href="/site_products/product_039/">
  <div class="product-thumb">
    <img src="https://shop-phinf.pstatic.net/20251028_82/1761631215994YUn7H_JPEG/11301190108030554_319270666.jpg" alt="2026년 벽걸이 달력" loading="lazy" />
    <div class="product-badge">39번</div>
  </div>
  <div class="product-body">
    <h3 class="product-title">2026년 벽걸이 달력</h3>
    <p class="product-summary">2026년 한눈에 확인 가능한 벽걸이 달력으로 새해 계획을 쉽게 세울 수 있습니다.…</p>
    <div class="product-cta"><span>자세히 보기 →</span></div>
  </div>
</a>
</div>
