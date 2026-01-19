import streamlit as st

# 페이지 설정
st.set_page_config(page_title="수의료 통합 수액 & 영양 계산기", layout="wide")

st.title("🐾 2024 AAHA 수액 & 영양 통합 계산기 (모바일 최적화)")
st.markdown("본 계산기는 **2024 AAHA Fluid Therapy Guidelines**와 **임상 아미노산 가이드**를 기반으로 합니다.")

# --- [1] 환자 기본 정보 입력 (모바일 대응을 위해 메인 페이지 상단 배치) ---
st.header("1. 환자 정보 및 질환 설정")
input_col1, input_col2, input_col3 = st.columns(3)

with input_col1:
    species = st.selectbox("품종 선택", ["개 (Dog)", "고양이 (Cat)"])
    weight = st.number_input("체중 (kg)", min_value=0.1, value=5.0, step=0.1)

with input_col2:
    dehydration = st.slider("탈수 정도 (%)", 0, 15, 0)
    # 기저 질환 선택
    has_heart = st.checkbox("심장병 (Heart Disease)")
    has_ckd = st.checkbox("만성 신부전 (CKD)")
    has_liver = st.checkbox("간질환 (Liver Disease)")

with input_col3:
    st.info("💡 **가이드라인 Tip**")
    if has_heart:
        st.caption("- 심장병 환자: 유지 수액량 50% 제한 권장")
    if has_ckd:
        st.caption("- 신부전 환자: 고염소혈증 및 수액 과부하 주의")

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
# 1. 수액량 계산
maint_rate = 50 # 사용자 요청 기본값
daily_maint = weight * maint_rate * (0.5 if has_heart else 1.0)
deficit_ml = weight * (dehydration / 100) * 1000
total_fluid_24h = daily_maint + deficit_ml
hourly_fluid_rate = total_fluid_24h / 24

# 2. 칼륨(K) 보충 정밀 로직 (AAHA Table 11 기반)
k_notices = []
k_mix_per_L = 0

if k < 3.5:
    # 안전 용량(mEq/kg/hr) 결정 
    if k < 2.0: dose_limit = 0.5
    elif k < 2.5: dose_limit = 0.3
    elif k < 3.0: dose_limit = 0.2
    else: dose_limit = 0.1
    
    # 1L 수액백에 추가해야 할 mEq 계산
    # 공식: (한계 용량 * 체중) / 시간당 수액속도 * 1000
    if hourly_fluid_rate > 0:
        k_mix_per_L = (dose_limit * weight) / hourly_fluid_rate * 1000
        # 최대 안전 보충량 제한 알림
        k_notices.append(f"⚠️ **저칼륨혈증**: 목표 용량 {dose_limit} mEq/kg/hr 기준")
        k_notices.append(f"👉 **1L 수액백당 {k_mix_per_L:.1f} mEq** 혼합하세요.")
        k_notices.append("🚨 **주의**: 투여 속도가 빨라지면 칼륨 농도를 즉시 낮춰야 합니다.")

# 3. 기타 수액 분석
notices = []
fluid_type = "완충 결정질액 (Hartmann 또는 Plasmasol)"

if cl > 120 or has_ckd:
    fluid_type = "Hartmann액 또는 Plasmasol (신장 보호)"
    notices.append("⚠️ **신장 보호**: 고염소혈증 방지를 위해 0.9% NaCl 사용 지양[cite: 783].")
if ica < 1.0:
    notices.append("⚠️ **저칼슘혈증**: 글루콘산 칼슘 별도 투여 검토 권장[cite: 784].")

# 결과 출력
res_col1, res_col2 = st.columns(2)
with res_col1:
    st.subheader("📊 수액 처방 결과")
    st.success(f"**총 수액량: {total_fluid_24h:.1f} mL/day**")
    st.metric("투여 속도", f"{hourly_fluid_rate:.1f} mL/hr")
    st.write(f"추천 수액: **{fluid_type}**")

with res_col2:
    st.subheader("📢 정밀 리포트")
    for kn in k_notices: st.warning(kn)
    for n in notices: st.write(n)
    if na > 0:
        osm = (2 * na) + (glu / 18) + (bun / 2.8)
        st.write(f"혈장 삼투압: **{osm:.1f} mOsm/L**")
        if osm > 350: st.error("🚨 HHS 고위험: 매우 신중한 수액 투여가 필요합니다.")

st.divider()

# --- [3] 아미노산(AA) 및 영양(PN) 설계 ---
st.header("3. 아미노산 및 비경구 영양(PN) 설계")
rer = 70 * (weight ** 0.75)
rer_pct = st.slider("목표 RER 비율 (%)", 33, 100, 33)
target_kcal = rer * (rer_pct / 100)

pn_col1, pn_col2 = st.columns(2)
with pn_col1:
    st.subheader("아미노산(AA) 공급")
    aa_start = 0.5 if (has_heart or has_ckd or has_liver) else 1.0
    aa_dose = st.number_input("AA 용량 (g/kg/day)", value=aa_start, step=0.1)
    aa_product = st.selectbox("제품 선택", ["네프리솔 (5.6%)", "10% 후라바솔", "후리바솔-헤파 (6.5%)"])
    
    conc_map = {"네프리솔 (5.6%)": 5.6, "10% 후라바솔": 10.0, "후리바솔-헤파 (6.5%)": 6.5}
    aa_ml = (weight * aa_dose / conc_map[aa_product]) * 100
    st.info(f"**{aa_product}**: {aa_ml:.1f} mL/day")

with pn_col2:
    st.subheader("NPC(비단백 칼로리) 구성")
    aa_kcal = (weight * aa_dose) * 4
    npc_kcal = max(0.0, target_kcal - aa_kcal)
    glu_ratio = st.slider("Dextrose 비율 (%)", 0, 100, 50)
    
    glu_ml = (npc_kcal * (glu_ratio / 100)) / 1.7
    lip_ml = (npc_kcal * ((100 - glu_ratio) / 100)) / 2.0
    st.info(f"**Dex 50%**: {glu_ml:.1f} mL | **Lipid 20%**: {lip_ml:.1f} mL")

st.divider()

# --- [4] 모니터링 ---
st.header("🚨 수액 과부하 감시 지표")
c1, c2, c3 = st.columns(3)
c1.checkbox("체중 증가 (>10%)")
c2.checkbox("호흡수/노력 증가")
c3.checkbox("비강 분비물/결막 부종")

st.caption("2024 AAHA Fluid Therapy Guidelines & User Specified Clinical Protocol")
