import streamlit as st

# 페이지 설정
st.set_page_config(page_title="수의료 통합 수액 & 영양 계산기", layout="wide")

st.title("🐾 2024 AAHA 수액 & 영양 통합 계산기 (v5.0)")
st.markdown("본 도구는 **2024 AAHA 가이드라인**과 병원 내 **조제 실무 프로토콜**을 완벽히 통합합니다.")

# --- [1] 환자 정보 및 수액백 설정 (메인 상단 배치) ---
st.header("1. 환자 정보 및 수액백 설정")
row1_col1, row1_col2, row1_col3 = st.columns(3)

with row1_col1:
    species = st.selectbox("품종", ["개 (Dog)", "고양이 (Cat)"])
    weight = st.number_input("체중 (kg)", min_value=0.1, value=5.0, step=0.1)

with row1_col2:
    # 수액백 규격 가변 적용 (500, 50, 30 mL)
    bag_size = st.selectbox("수액백 규격 선택 (mL)", [500, 50, 30])
    dehydration = st.slider("탈수 정도 (%)", 0, 15, 0)

with row1_col3:
    has_heart = st.checkbox("심장병 (수액 제한)")
    has_ckd = st.checkbox("만성 신부전 (염소 주의)")
    has_liver = st.checkbox("간질환 (AA 선택 주의)")

st.divider()

# --- [2] 전해질 분석 및 수액 설계 ---
st.header("2. 전해질 정밀 분석 및 수액 설계")
e_col1, e_col2, e_col3 = st.columns(3)

with e_col1:
    na = st.number_input("Na (mEq/L)", value=145.0)
    k_val = st.number_input("K (mEq/L)", value=4.0)
with e_col2:
    cl = st.number_input("Cl (mEq/L)", value=110.0)
    ica = st.number_input("iCa (mmol/L)", value=1.2)
with e_col3:
    glu = st.number_input("Glucose (mg/dL)", value=100.0)
    bun = st.number_input("BUN (mg/dL)", value=20.0)

# --- 계산 로직 ---
# 1. 수액량 계산
maint_vol = weight * 50 * (0.5 if has_heart else 1.0) # 심장병 시 50% 제한 [cite: 634]
deficit_vol = weight * (dehydration / 100) * 1000 # 탈수 교정량 [cite: 312]
total_fluid = maint_vol + deficit_vol
hourly_rate = total_fluid / 24

# 2. KCl 정밀 희석 로직 (2 mEq/mL 제품 기준)
k_msg = []
if k_val < 3.5 and hourly_rate > 0:
    # 안전 투여 한계 설정 (mEq/kg/hr) 
    if k_val < 2.0: k_limit = 0.5
    elif k_val < 2.5: k_limit = 0.3
    elif k_val < 3.0: k_limit = 0.2
    else: k_limit = 0.1
    
    # 선택된 수액백 사이즈에 맞는 mL 계산
    # 공식: (한계 * 체중 / 시간당속도) * 백사이즈 = 백당 mEq -> /2 = mL
    k_meq_for_bag = (k_limit * weight / hourly_rate) * bag_size
    k_ml_for_bag = k_meq_for_bag / 2 
    
    k_msg.append(f"⚠️ **저칼륨혈증**: 안전 한계 {k_limit} mEq/kg/hr 기준")
    k_msg.append(f"👉 **{bag_size}mL 수액백에 KCl {k_ml_for_bag:.1f} mL 혼합** ({k_meq_for_bag:.1f} mEq)")

# 결과 출력
res_col1, res_col2 = st.columns(2)
with res_col1:
    st.subheader("📊 수액 처방 결과")
    st.success(f"**총 수액량: {total_fluid:.1f} mL/day**")
    st.metric("권장 투여 속도", f"{hourly_rate:.1f} mL/hr")
    st.write(f"추천 수액: **{'Hartmann액 또는 Plasmasol' if cl > 120 or has_ckd else 'Hartmann/Plasmasol'}**")

with res_col2:
    st.subheader("📢 임상 분석 리포트")
    for km in k_msg: st.warning(km)
    if na > 0:
        osm = (2 * na) + (glu / 18) + (bun / 2.8)
        st.write(f"계산된 혈장 삼투압: **{osm:.1f} mOsm/L**")
        if osm > 350: st.error("🚨 HHS 위험: 정밀한 속도 제어와 모니터링이 필요합니다!")

st.divider()

# --- [3] 아미노산(AA) 및 영양(PN) 설계 ---
st.header("3. 아미노산 및 비경구 영양(PN) 설계")
rer = 70 * (weight ** 0.75) # 기초 대사량 [cite: 456]
target_kcal = rer * (st.slider("목표 RER 비율 (%)", 33, 100, 33) / 100)

pn_col1, pn_col2 = st.columns(2)
with pn_col1:
    st.subheader("아미노산(AA) 설정")
    aa_start = 0.5 if (has_heart or has_ckd or has_liver) else 1.0
    aa_dose = st.number_input("AA 목표 용량 (g/kg/day)", value=aa_start, step=0.1)
    aa_prod = st.selectbox("제품 선택", ["네프리솔 (5.6% - 신장)", "10% 후라바솔 (고용량)", "후리바솔-헤파 (6.5% - 간)"])
    
    conc_map = {"네프리솔 (5.6% - 신장)": 5.6, "10% 후라바솔 (고용량)": 10.0, "후리바솔-헤파 (6.5% - 간)": 6.5}
    aa_ml = (weight * aa_dose / conc_map[aa_prod]) * 100
    st.info(f"**{aa_product if 'aa_product' in locals() else aa_prod}**: {aa_ml:.1f} mL/day")

with pn_col2:
    st.subheader("NPC (비단백 칼로리) 구성")
    aa_kcal = (weight * aa_dose) * 4
    npc_kcal = max(0.0, target_kcal - aa_kcal)
    glu_pct = st.slider("포도당 비중 (%)", 0, 100, 50)
    
    glu_ml = (npc_kcal * (glu_pct / 100)) / 1.7
    lip_ml = (npc_kcal * ((100 - glu_pct) / 100)) / 2.0
    st.info(f"**Dex 50%**: {glu_ml:.1f} mL | **Lipid 20%**: {lip_ml:.1f} mL")

st.divider()

# --- [4] 수액 과부하 모니터링 ---
st.header("🚨 수액 과부하 감시 지표")
c1, c2, c3 = st.columns(3)
c1.checkbox("체중 증가 (전일 대비 >10%)")
c2.checkbox("호흡수 및 호흡 노력 증가")
c3.checkbox("비강 분비물 또는 결막 부종")

st.caption("Reference: 2024 AAHA Fluid Therapy Guidelines & Hospital Protocol (Hartmann/Plasmasol/AA/KCl)")

