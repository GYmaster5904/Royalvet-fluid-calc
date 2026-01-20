import streamlit as st

# [1] 페이지 설정 및 보안 강화 (상단 메뉴 및 GitHub 아이콘 숨기기)
st.set_page_config(page_title="수의료 통합 수액 & 영양 계산기", layout="wide")

# CSS 주입으로 상단 헤더, 메뉴, 배포 버튼을 완전히 제거합니다.
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    .stAppDeployButton {display:none;}
    [data-testid="stHeader"] {display:none;}
    </style>
    """, unsafe_allow_html=True)

st.title("🐾 2024 AAHA 수액 & 영양 통합 계산기 (v14.0)")
st.markdown("본 도구는 **2024 AAHA 가이드라인**과 **병원 전용 조제 프로토콜**을 기반으로 한 최종 통합 버전입니다.")

# --- [2] 1단계: 환자 정보 및 수액백 설정 (모바일 최적화) ---
st.header("1. 환자 정보 및 수액백 설정")
col1, col2, col3 = st.columns(3)

with col1:
    species = st.selectbox("품종", ["개 (Dog)", "고양이 (Cat)"])
    weight = st.number_input("체중 (kg)", min_value=0.1, value=5.0, step=0.1)

with col2:
    # 수액백 규격 선택: 500mL를 기본값(index=1)으로 설정
    bag_size = st.selectbox("수액백 규격 선택 (mL)", [1000, 500, 100, 50, 30], index=1)
    dehydration = st.slider("탈수 정도 (%)", 0, 15, 0)

with col3:
    has_heart = st.checkbox("심장병 (수액 50% 제한)")
    has_ckd = st.checkbox("만성 신부전 (Cl 농도 주의)")
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
    st.caption("P(인)는 모니터링 수치입니다.")

# --- 수액 및 전해질 계산 로직 ---

# 1. 수액량 및 속도 계산
# 심장병 환자: 유지 수액량을 50%로 제한 [cite: 634]
maint_vol = weight * 50 * (0.5 if has_heart else 1.0) 
deficit_vol = weight * (dehydration / 100) * 1000 # [cite: 312]
total_fluid = maint_vol + deficit_vol
hourly_rate = total_fluid / 24

# 2. 임상 분석 리포트 알림 생성
notices = []

# (1) KCl 보정 로직 (2 mEq/mL 제품 기준)
# 시간당 투여 한계(mEq/kg/hr)를 넘지 않도록 속도 연동 계산 [cite: 729]
if k_val < 3.5 and hourly_rate > 0:
    if k_val < 2.0: k_safe = 0.5
    elif k_val < 2.5: k_safe = 0.35
    elif k_val < 3.0: k_safe = 0.22
    else: k_safe = 0.12
    
    # 1L당 필요 mEq 역산 후 선택된 백 사이즈에 맞게 조절
    needed_meq_for_bag = (k_safe * weight / hourly_rate) * bag_size
    needed_ml_for_bag = needed_meq_for_bag / 2 # 2mEq/mL
    notices.append(f"⚠️ **저칼륨혈증**: {bag_size}mL 백에 **KCl {needed_ml_for_bag:.1f} mL** 혼합 추천")
    notices.append(f"   (안전 한계 {k_safe} mEq/kg/hr 기준)")

# (2) iCa 보정 (10% Calcium Gluconate 추천 고정량 적용)
if ica < 1.1 and ica > 0:
    ca_bolus = weight * 1.0 # 1.0 mL/kg 고정
    ca_cri = weight * 0.5   # 0.5 mL/kg/hr 고정
    notices.append(f"🚨 **저칼슘혈증**: 10% Ca Gluconate **Bolus {ca_bolus:.1f} mL** (20분간 서서히)")
    notices.append(f"🏥 **추천 CRI**: 10% Ca Gluconate **{ca_cri:.1f} mL/hr** 주입 권장")

# (3) 수액 종류 추천 (Hartmann vs Plasmasol)
# Cl 수치가 높거나 CKD 환자인 경우, Cl 농도가 더 낮은 Plasmasol을 강력 추천 
if cl > 115 or has_ckd:
    fluid_rec = "Plasmasol (신장 보호용 낮은 Cl 농도)"
    notices.append("💡 **수액 선택**: 고염소혈증/신부전 상태이므로 Cl이 낮은 **Plasmasol**이 Hartmann보다 유리합니다.")
else:
    fluid_rec = "Hartmann액 (하트만) 또는 Plasmasol"

# 결과 출력
res_col1, res_col2 = st.columns(2)
with res_col1:
    st.subheader("📊 수액 처방 결과")
    st.success(f"**총 수액량: {total_fluid:.1f} mL/day**")
    st.metric(f"{bag_size}mL 백 기준 속도", f"{hourly_rate:.1f} mL/hr")
    st.write(f"추천 수액: **{fluid_rec}**")

with res_col2:
    st.subheader("📢 임상 정밀 리포트")
    for n in notices: st.warning(n)
    if na > 0:
        # 유효 삼투압 공식 [cite: 229]
        osm = (2 * na) + (glu / 18) + (bun / 2.8)
        st.write(f"계산된 유효 삼투압: **{osm:.1f} mOsm/L**")
        if osm > 350: st.error("🚨 HHS 고위험: 수액 투여 속도를 매우 신중하게 조절하세요.")

st.divider()

# --- [4] 3단계: 아미노산 및 영양(PN) 설계 ---
st.header("3. 아미노산 및 비경구 영양(PN) 설계")
rer = 70 * (weight ** 0.75)
target_kcal = rer * (st.slider("목표 RER 비율 (%)", 33, 100, 33) / 100)

pn_col1, pn_col2 = st.columns(2)
with pn_col1:
    st.subheader("아미노산(AA) 설정")
    # 질환 동반 시 보수적 시작 용량 적용 (0.5 g/kg)
    is_complex = has_heart or has_ckd or has_liver
    aa_start = 0.5 if is_complex else 1.0
    aa_dose = st.number_input("AA 목표 용량 (g/kg/day)", value=aa_start, step=0.1)
    aa_prod = st.selectbox("제품 선택", ["네프리솔 (5.6%)", "10% 후라바솔", "후리바솔-헤파 (6.5%)"])
    
    conc_map = {"네프리솔 (5.6%)": 5.6, "10% 후라바솔": 10.0, "후리바솔-헤파 (6.5%)": 6.5}
    aa_ml_total = (weight * aa_dose / conc_map[aa_prod]) * 100
    st.info(f"**{aa_prod} 필요량**: {aa_ml_total:.1f} mL/day")

with pn_col2:
    st.subheader("NPC (비단백 칼로리) 구성")
    aa_kcal = (weight * aa_dose) * 4
    npc_kcal = max(0.0, target_kcal - aa_kcal)
    glu_ratio = st.slider("포도당(Dextrose) 비중 (%)", 0, 100, 50)
    
    # 50% Dextrose(1.7 kcal/mL), 20% Lipid(2.0 kcal/mL) 기준
    glu_ml_res = (npc_kcal * (glu_ratio / 100)) / 1.7
    lip_ml_res = (npc_kcal * ((100 - glu_ratio) / 100)) / 2.0
    st.info(f"**Dex 50%**: {glu_ml_res:.1f} mL | **Lipid 20%**: {lip_ml_res:.1f} mL")

st.divider()

# --- [5] 모니터링 ---
st.header("🚨 수액 과부하 감시 지표")
c1, c2, c3 = st.columns(3)
c1.checkbox("체중 증가 (전일 대비 >10%)")
c2.checkbox("호흡수 및 노력 증가")
c3.checkbox("비강 분비물 또는 결막 부종")

st.caption("Reference: 2024 AAHA Guidelines & Hospital Internal Protocols (v14.0)")

