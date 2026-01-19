import streamlit as st

# 페이지 설정
st.set_page_config(page_title="수의료 통합 수액 & 영양 계산기", layout="wide")

st.title("🐾 2024 AAHA 가이드라인 & 영양(PN) 통합 계산기")
st.markdown("본 도구는 **2024 AAHA Fluid Therapy Guidelines**와 **병원 전용 수액(Hartmann, Plasmasol)** 및 **아미노산 프로토콜**을 통합한 결과물입니다.")

# --- [1] 사이드바: 환자 및 질환 설정 ---
st.sidebar.header("1. 환자 정보 입력")
species = st.sidebar.selectbox("품종", ["개 (Dog)", "고양이 (Cat)"])
weight = st.sidebar.number_input("체중 (kg)", min_value=0.1, value=5.0, step=0.1)
dehydration = st.sidebar.slider("탈수 정도 (%)", 0, 15, 0)

st.sidebar.header("2. 기저 질환 (Risk Factors)")
has_heart = st.sidebar.checkbox("심장병 (Heart Disease)")
has_ckd = st.sidebar.checkbox("만성 신부전 (CKD)")
has_liver = st.sidebar.checkbox("간질환 (Liver Disease)")
is_complex = has_heart or has_ckd or has_liver

# --- [2] 전해질 분석 및 수액 요법 설계 ---
st.header("💧 [Step 1] 전해질 정밀 분석 및 수액 설계")
st.caption("환자의 혈청 전해질 수치를 입력하면 가이드라인에 따른 최적의 수액과 보충량을 제안합니다.")

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

# 전해질 기반 처방 로직
notices = []
fluid_type = "완충 결정질액 (Hartmann 또는 Plasmasol)"

# 1. 칼륨(K) 보충 로직 (AAHA Table 11)
if k < 3.5:
    if k < 2.0: k_mix, rate_limit = "200 mEq/L", "0.5 mEq/kg/hr"
    elif k < 2.5: k_mix, rate_limit = "120-160 mEq/L", "0.3-0.4 mEq/kg/hr"
    elif k < 3.0: k_mix, rate_limit = "80-100 mEq/L", "0.2-0.25 mEq/kg/hr"
    else: k_mix, rate_limit = "40-60 mEq/L", "0.1-0.15 mEq/kg/hr"
    notices.append(f"⚠️ **저칼륨혈증**: $KCl$ {k_mix} 보충 권장. (속도 제한: {rate_limit})")

# 2. 염소(Cl) 및 신장 보호 로직
if cl > 120 or has_ckd:
    fluid_type = "Hartmann(하트만)액 또는 Plasmasol"
    notices.append("⚠️ **신장 보호**: 고염소혈증 방지를 위해 $0.9\%~NaCl$ 사용을 금지하고 완충 수액을 사용하세요.")

# 3. 칼슘(iCa) 로직
if ica < 1.0:
    notices.append(f"⚠️ **저칼슘혈증**: Hartmann액의 칼슘 함량(약 2.7 mEq/L)만으로는 교정이 불충분합니다. 추가 보충을 고려하세요.")

# 수액량 계산 (사용자 요청 50ml/kg & 질환별 제한)
maint_vol = weight * 50 * (0.5 if has_heart else 1.0)
deficit_vol = weight * (dehydration / 100) * 1000
total_fluid = maint_vol + deficit_vol

res_col1, res_col2 = st.columns(2)
with res_col1:
    st.subheader("📊 일일 수액 목표")
    st.success(f"**총 수액량: {total_fluid:.1f} mL/day ({total_fluid/24:.1f} mL/hr)**")
    st.write(f"권장 수액: **{fluid_type}**")
    if has_heart: st.warning("심장 질환으로 인해 유지 수액량을 50%로 제한하였습니다.")

with res_col2:
    st.subheader("📢 임상 분석 리포트")
    for n in notices: st.write(n)
    if na > 0:
        osm = (2 * na) + (glu / 18) + (bun / 2.8)
        st.write(f"계산된 유효 삼투압: **{osm:.1f} mOsm/L**")
        if osm > 350: st.error("🚨 HHS 고위험군: 수액 속도를 매우 천천히 조절하고 정밀 모니터링이 필요합니다!")

st.divider()

# --- [3] 영양(RER) 및 비경구 영양(PN) 설계 ---
st.header("🍴 [Step 2] 아미노산 및 비경구 영양(PN) 설계")
rer = 70 * (weight ** 0.75)
rer_pct = st.slider("목표 RER 공급 비율 (%)", 33, 100, 33)
target_kcal = rer * (rer_pct / 100)

pn_col1, pn_col2 = st.columns(2)
with pn_col1:
    st.subheader("1. 아미노산(AA) 공급 계획")
    # 질환별 보수적 용량 설정
    aa_start = 0.5 if is_complex else 1.0
    aa_dose = st.number_input("AA 목표 용량 (g/kg/day)", value=aa_start, step=0.1)
    aa_product = st.selectbox("사용 제품 선택", ["네프리솔 (5.6% - 신장)", "10% 후라바솔 (고용량)", "후리바솔-헤파 (6.5% - 간)"])
    
    conc_map = {"네프리솔 (5.6% - 신장)": 5.6, "10% 후라바솔 (고용량)": 10.0, "후리바솔-헤파 (6.5% - 간)": 6.5}
    total_aa_g = weight * aa_dose
    aa_ml = (total_aa_g / conc_map[aa_product]) * 100
    aa_kcal = total_aa_g * 4
    
    st.info(f"**{aa_product} 필요량: {aa_ml:.1f} mL/day**")
    st.write(f"(단백질 공급량: {total_aa_g:.1f} g / {aa_kcal:.1f} kcal)")

with pn_col2:
    st.subheader("2. 비단백 칼로리(NPC) 구성")
    npc_kcal = max(0.0, target_kcal - aa_kcal)
    glu_ratio = st.slider("포도당(Dextrose) 비중 (%)", 0, 100, 50)
    
    # 에너지 밀도: Dex 50%(1.7 kcal/mL), Lipid 20%(2.0 kcal/mL)
    glu_ml = (npc_kcal * (glu_ratio / 100)) / 1.7
    lip_ml = (npc_kcal * ((100 - glu_ratio) / 100)) / 2.0
    
    st.write(f"비단백 칼로리 필요량: {npc_kcal:.1f} kcal")
    st.info(f"**Dextrose 50%**: {glu_ml:.1f} mL")
    st.info(f"**Lipid 20%**: {lip_ml:.1f} mL")
    st.success(f"**영양 수액(PN) 총 볼륨: {aa_ml + glu_ml + lip_ml:.1f} mL/day**")

st.divider()

# --- [4] 수액 과부하 모니터링 ---
st.header("🚨 수액 과부하(Fluid Overload) 감시")
st.error("주의: 신부전, 심장병, 간질환 환자는 수액 과부하에 매우 취약합니다.")
c1, c2, c3 = st.columns(3)
c1.checkbox("체중 증가 (전일 대비 >10%)")
c2.checkbox("호흡수 및 호흡 노력 증가")
c3.checkbox("장액성 비강 분비물 또는 결막 부종")

st.caption("Ref: 2024 AAHA Fluid Therapy Guidelines & Hospital Protocol (Hartmann/Plasmasol/AA)")
