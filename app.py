import streamlit as st

# 페이지 설정
st.set_page_config(page_title="수의료 통합 수액 & 영양 계산기", layout="wide")

st.title("🐾 2024 AAHA 수액 & 영양 통합 계산기 (v3.0)")
st.markdown("본 도구는 **2024 AAHA 가이드라인** 및 **병원 실무 프로토콜**을 기반으로 검토되었습니다.")

# --- [1] 환자 기본 정보 및 질환 설정 (모바일 대응 메인 상단 배치) ---
st.header("1. 환자 정보 및 질환 설정")
st.caption("모바일 사용 시 상단에서 정보를 바로 입력하세요.")
row1_col1, row1_col2, row1_col3 = st.columns(3)

with row1_col1:
    species = st.selectbox("품종", ["개 (Dog)", "고양이 (Cat)"])
    weight = st.number_input("체중 (kg)", min_value=0.1, value=5.0, step=0.1)

with row1_col2:
    dehydration = st.slider("탈수 정도 (%)", 0, 15, 0)
    has_heart = st.checkbox("심장병 (수액 제한 대상)")
    has_ckd = st.checkbox("만성 신부전 (Cl 제한 대상)")
    has_liver = st.checkbox("간질환 (AA 제한 대상)")

with row1_col3:
    st.info("💡 **환자별 조절 사항**")
    if has_heart: st.caption("- 심장 환자: 유지량 50% 제한 적용")
    if has_ckd: st.caption("- 신부전 환자: 하트만/플라즈마솔 권장")
    if has_liver: st.caption("- 간질환 환자: 후리바솔-헤파 권장")

st.divider()

# --- [2] 전해질 분석 및 정밀 수액 설계 ---
st.header("2. 전해질 정밀 분석 및 수액 설계")
e_col1, e_col2, e_col3 = st.columns(3)

with e_col1:
    na = st.number_input("Na (mEq/L)", value=145.0)
    k = st.number_input("K (mEq/L)", value=4.0)
with e_col2:
    cl = st.number_input("Cl (mEq/L)", value=110.0)
    ica = st.number_input("iCa (mmol/L)", value=1.2)
with e_col3:
    glu = st.number_input("Glucose (mg/dL)", value=100.0)
    bun = st.number_input("BUN (mg/dL)", value=20.0)

# --- 수액량 및 로직 계산 시작 ---
# 1. 수액량 계산 (AAHA Table 9 기반)
maint_rate = 50 # 사용자 지정 기본값
daily_maint = weight * maint_rate * (0.5 if has_heart else 1.0)
deficit_ml = weight * (dehydration / 100) * 1000
total_fluid_24h = daily_maint + deficit_ml
hourly_rate = total_fluid_24h / 24

# 2. 칼륨(K) 보충 정밀 로직 (2 mEq/mL 제품 기준)
k_notices = []
if k < 3.5 and hourly_rate > 0:
    # 가이드라인 기반 mEq/kg/hr 안전 한계 설정
    if k < 2.0: k_safe_limit = 0.5
    elif k < 2.5: k_safe_limit = 0.3
    elif k < 3.0: k_safe_limit = 0.2
    else: k_safe_limit = 0.1
    
    # 1L 수액백에 혼합할 mL 역산 (안전 한계 기준)
    # 공식: (한계용량 * 체중) / (시간당수액량 / 1000) = 1L당 필요 mEq
    needed_meq_per_L = (k_safe_limit * weight) / (hourly_rate / 1000)
    needed_ml_per_L = needed_meq_per_L / 2 # 2 mEq/mL 제품 기준
    
    k_notices.append(f"⚠️ **저칼륨혈증**: 안전 한계 {k_safe_limit} mEq/kg/hr 기준")
    k_notices.append(f"👉 **1L 수액백에 KCl {needed_ml_per_L:.1f} mL 혼합** ({needed_meq_per_L:.1f} mEq)")
    k_notices.append("🚨 **주의**: 수액 속도를 높이면 칼륨 농도를 즉시 낮추어야 합니다!")

# 3. 기타 수액 분석
fluid_type = "완충 결정질액 (Hartmann 또는 Plasmasol)"
if cl > 120 or has_ckd:
    fluid_type = "Hartmann액 또는 Plasmasol (신장 보호)"

# 결과 출력
res_col1, res_col2 = st.columns(2)
with res_col1:
    st.subheader("📊 수액 처방 결과")
    st.success(f"**총 수액량: {total_fluid_24h:.1f} mL/day**")
    st.metric("권장 투여 속도", f"{hourly_rate:.1f} mL/hr")
    st.write(f"추천 수액: **{fluid_type}**")

with res_col2:
    st.subheader("📢 임상 분석 리포트")
    for kn in k_notices: st.warning(kn)
    if na > 0:
        osm = (2 * na) + (glu / 18) + (bun / 2.8)
        st.write(f"계산된 유효 삼투압: **{osm:.1f} mOsm/L**")
        if osm > 350: st.error("🚨 HHS 위험: 수액을 매우 천천히 투여하고 모니터링하세요.")

st.divider()

# --- [3] 아미노산(AA) 및 영양(PN) 설계 ---
st.header("3. 아미노산 및 비경구 영양(PN) 설계")
rer = 70 * (weight ** 0.75)
target_kcal = rer * (st.slider("목표 RER (%)", 33, 100, 33) / 100)

pn_col1, pn_col2 = st.columns(2)
with pn_col1:
    st.subheader("아미노산(AA) 공급")
    aa_start = 0.5 if (has_heart or has_ckd or has_liver) else 1.0
    aa_dose = st.number_input("AA 용량 (g/kg/day)", value=aa_start, step=0.1)
    aa_prod = st.selectbox("제품 선택", ["네프리솔 (5.6% - 신장용)", "10% 후라바솔 (고용량)", "후리바솔-헤파 (6.5% - 간용)"])
    
    conc_map = {"네프리솔 (5.6% - 신장용)": 5.6, "10% 후라바솔 (고용량)": 10.0, "후리바솔-헤파 (6.5% - 간용)": 6.5}
    aa_ml = (weight * aa_dose / conc_map[aa_prod]) * 100
    st.info(f"**{aa_prod} 필요량: {aa_ml:.1f} mL/day**")

with pn_col2:
    st.subheader("비단백 칼로리(NPC) 구성")
    aa_kcal = (weight * aa_dose) * 4
    npc_kcal = max(0.0, target_kcal - aa_kcal)
    glu_ratio = st.slider("포도당(Dextrose) 비율 (%)", 0, 100, 50)
    
    glu_ml = (npc_kcal * (glu_ratio / 100)) / 1.7
    lip_ml = (npc_kcal * ((100 - glu_ratio) / 100)) / 2.0
    st.info(f"**Dex 50%**: {glu_ml:.1f} mL | **Lipid 20%**: {lip_ml:.1f} mL")

st.divider()

# --- [4] 모니터링 ---
st.header("🚨 수액 과부하 감시 지표")
c1, c2, c3 = st.columns(3)
c1.checkbox("체중 증가 (전일 대비 >10%)")
c2.checkbox("호흡수 및 호흡 노력 증가")
c3.checkbox("비강 분비물 또는 결막 부종")

st.caption("Reference: 2024 AAHA Fluid Therapy Guidelines & Hospital Internal Protocol (Hartmann, Plasmasol, 2 mEq/mL KCl)")
