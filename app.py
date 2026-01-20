import streamlit as st

# [1] 페이지 설정 및 보안 (GitHub 메뉴 및 편집 버튼 숨기기)
st.set_page_config(page_title="2024 AAHA 수액 & 영양 계산기", layout="wide")

# CSS 주입으로 상단 헤더, 메뉴, 배포 버튼을 숨깁니다.
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    .stAppDeployButton {display:none;}
    [data-testid="stHeader"] {display:none;}
    </style>
    """, unsafe_allow_html=True)

st.title("🐾 2024 AAHA 수액 & 영양 통합 계산기 (v13.0)")
st.markdown("본 도구는 **2024 AAHA 가이드라인**과 **병원 조제 실무**를 반영한 최종 보안 버전입니다.")

# --- [2] 1단계: 환자 정보 및 수액백 설정 ---
st.header("1. 환자 정보 및 수액백 설정")
col1, col2, col3 = st.columns(3)

with col1:
    species = st.selectbox("품종", ["개 (Dog)", "고양이 (Cat)"])
    weight = st.number_input("체중 (kg)", min_value=0.1, value=5.0, step=0.1)

with col2:
    # 수액백 규격 선택: 기본값 500mL
    bag_size = st.selectbox("수액백 규격 선택 (mL)", [1000, 500, 100, 50, 30], index=1)
    dehydration = st.slider("탈수 정도 (%)", 0, 15, 0)

with col3:
    has_heart = st.checkbox("심장병 (수액 50% 제한)")
    has_ckd = st.checkbox("만성 신부전 (염소 주의)")
    has_liver = st.checkbox("간질환 (AA 선택 주의)")

st.divider()

# --- [3] 2단계: 전해질 및 검사 수치 분석 ---
st.header("2. 전해질 및 검사 수치 분석")
e_col1, e_col2, e_col3, e_col4 = st.columns(4)

with e_col1:
    na = st.number_input("Na (mEq/L)", value=145.0)
    k_val = st.number_input("K (mEq/L)", value=4.0)
with e_col2:
    cl = st.number_input("Cl (mEq/L)", value=110.0)
    ica = st.number_input("iCa (mmol/L)", value=1.2)
with e_col3:
    glu = st.number_input("Glucose (mg/dL)", value=100.0)
    bun = st.number_input("BUN (mg/dL)", value=20.0)
with e_col4:
    phos = st.number_input("P (mg/dL)", value=4.0)
    st.caption("인(P)은 모니터링 수치입니다.")

# --- 수액 및 전해질 계산 로직 ---
# 1. 수액량 계산
maint_vol = weight * 50 * (0.5 if has_heart else 1.0) # 심장병 시 유지량 50% 제한
deficit_vol = weight * (dehydration / 100) * 1000
total_fluid = maint_vol + deficit_vol
hourly_rate = total_fluid / 24

# 2. 전해질 보정 정밀 리포트
notices = []

# 칼륨(K) 보정 로직 (AAHA Table 11 기반)
if k_val < 3.5 and hourly_rate > 0:
    # 가이드라인의 mEq/kg/hr 안전 한계치 적용
    if k_val < 2.0: k_safe_limit = 0.5
    elif k_val < 2.5: k_safe_limit = 0.35 # 중간값 적용
    elif k_val < 3.0: k_safe_limit = 0.22 # 중간값 적용
    else: k_safe_limit = 0.12 # 중간값 적용
    
    # 공식: (한계치 * 체중) / (시간당 수액량 / 1000) = 1L당 필요 mEq
    # (결과 * 백사이즈/1000) / 2 = 필요 mL (2mEq/mL KCl 기준)
    needed_meq_per_bag = (k_safe_limit * weight / hourly_rate) * bag_size
    needed_ml_per_bag = needed_meq_per_bag / 2
    
    notices.append(f"⚠️ **저칼륨혈증**: {bag_size}mL 백에 **KCl {needed_ml_per_bag:.1f} mL** 혼합 추천")
    notices.append(f"   (공급 속도: {k_safe_limit} mEq/kg/hr 기준)")

# iCa 보정 (추천 고정 용량 적용)
if ica < 1.1 and ica > 0:
    ca_bolus = weight * 1.0 # 1.0 mL/kg 고정
    ca_cri = weight * 0.5   # 0.5 mL/kg/hr 고정
    notices.append(f"🚨 **저칼슘혈증**: 10% Ca Gluconate **추천 Bolus {ca_bolus:.1f} mL** (20분간 서서히)")
    notices.append(f"🏥 **추천 CRI**: 10% Ca Gluconate **{ca_cri:.1f} mL/hr** 주입 권장")

# 결과 출력
res_col1, res_col2 = st.columns(2)
with res_col1:
    st.subheader("📊 수액 처방 결과")
    st.success(f"**총 수액 목표량: {total_fluid:.1f} mL/day**")
    st.metric(f"{bag_size}mL 백 기준 속도", f"{hourly_rate:.1f} mL/hr")
    st.write(f"추천 수액: **{'Hartmann/Plasmasol' if cl > 120 or has_ckd else 'Hartmann액'}**")

with res_col2:
    st.subheader("📢 임상 정밀 리포트")
    for n in notices: st.warning(n)
    if na > 0:
        osm = (2 * na) + (glu / 18) + (bun / 2.8)
        st.write(f"계산된 유효 삼투압: **{osm:.1f} mOsm/L**")
        if osm > 350: st.error("🚨 HHS 위험: 수액 속도를 매우 신중하게 조절하십시오.")

st.divider()

# --- [4] 3단계: 아미노산 및 영양(PN) 설계 ---
st.header("3. 아미노산 및 비경구 영양(PN) 설계")
rer = 70 * (weight ** 0.75)
target_kcal = rer * (st.slider("목표 RER 비율 (%)", 33, 100, 33) / 100)

pn_col1, pn_col2 = st.columns(2)
with pn_col1:
    st.subheader("아미노산(AA) 설정")
    is_complex = has_heart or has_ckd or has_liver
    aa_start = 0.5 if is_complex else 1.0
    aa_dose = st.number_input("AA 목표 용량 (g/kg/day)", value=aa_start, step=0.1)
    aa_prod = st.selectbox("제품 선택", ["네프리솔 (5.6%)", "10% 후라바솔", "후리바솔-헤파 (6.5%)"])
    
    conc_map = {"네프리솔 (5.6%)": 5.6, "10% 후라바솔": 10.0, "후리바솔-헤파 (6.5%)": 6.5}
    aa_ml_calc = (weight * aa_dose / conc_map[aa_prod]) * 100
    st.info(f"**{aa_prod} 필요량**: {aa_ml_calc:.1f} mL/day")

with pn_col2:
    st.subheader("NPC (비단백 칼로리) 구성")
    aa_kcal = (weight * aa_dose) * 4
    npc_kcal = max(0.0, target_kcal - aa_kcal)
    glu_ratio = st.slider("포도당(Dextrose) 비중 (%)", 0, 100, 50)
    
    glu_ml_final = (npc_kcal * (glu_ratio / 100)) / 1.7
    lip_ml_final = (npc_kcal * ((100 - glu_ratio) / 100)) / 2.0
    st.info(f"**Dex 50%**: {glu_ml_final:.1f} mL | **Lipid 20%**: {lip_ml_final:.1f} mL")

st.divider()

# --- [5] 모니터링 ---
st.header("🚨 수액 과부하 감시 지표")
c1, c2, c3 = st.columns(3)
c1.checkbox("체중 급증 (전일 대비 >10%)")
c2.checkbox("호흡수 및 노력 증가")
c3.checkbox("비강 분비물 또는 결막 부종")

st.caption("Reference: 2024 AAHA Guidelines & Hospital Internal Protocols (v13.0)")

