import streamlit as st

# 페이지 설정
st.set_page_config(page_title="2024 AAHA 수액 & 영양 계산기", layout="wide")

st.title("🐾 2024 AAHA 가이드라인 & 비경구 영양(PN) 통합 계산기")
st.markdown("""
이 계산기는 **2024 AAHA Fluid Therapy Guidelines**와 **임상 아미노산 투여 가이드**를 바탕으로 제작되었습니다.
""")

# --- [1] 사이드바: 환자 기본 정보 및 질환 ---
st.sidebar.header("1. 환자 정보 입력")
species = st.sidebar.selectbox("품종 선택", ["개 (Dog)", "고양이 (Cat)"])
weight = st.sidebar.number_input("체중 (kg)", min_value=0.1, value=5.0, step=0.1)
dehydration = st.sidebar.slider("탈수 정도 (%)", 0, 15, 0)

st.sidebar.header("2. 기저 질환 (Risk Factors)")
has_heart = st.sidebar.checkbox("심장병 (Heart Disease)")
has_ckd = st.sidebar.checkbox("만성 신부전 (CKD)")
has_liver = st.sidebar.checkbox("간질환 (Liver Disease)")

is_complex = has_heart or has_ckd or has_liver

# --- [2] 수액 요법 (Fluid Therapy) ---
st.header("💧 [Step 1] 수액 요법 설계")
col1, col2 = st.columns(2)

with col1:
    # AAHA Table 9 참고 유지량 (사용자 요청 50ml/kg 반영)
    maint_rate = 50
    daily_maint = weight * maint_rate
    
    # 질환별 제한 로직
    if has_heart:
        daily_maint *= 0.5  # 심장병 환자 0.5~1배 제한 권고 [cite: 634]
        st.warning("⚠️ 심장병 환자: 유지 수액량을 50%로 제한하고 0.45% NaCl + 2.5% Dex 사용을 고려하세요. [cite: 634]")
    
    # 탈수 교정량 (Box 3) [cite: 312]
    deficit_ml = weight * (dehydration / 100) * 1000
    total_fluid_24h = daily_maint + deficit_ml
    
    st.subheader("📊 수액 계산 결과")
    st.write(f"- 일일 유지량: {daily_maint:.1f} mL")
    st.write(f"- 탈수 교정량: {deficit_ml:.1f} mL")
    st.success(f"**24시간 총 수액 목표량: {total_fluid_24h:.1f} mL ({total_fluid_24h/24:.1f} mL/hr)**")

with col2:
    st.subheader("🧪 전해질 & 삼투압 감시")
    na = st.number_input("Na (mEq/L)", value=145.0)
    glu = st.number_input("Glucose (mg/dL)", value=100.0)
    bun = st.number_input("BUN (mg/dL)", value=20.0)
    
    if na > 0:
        # 유효 삼투압 공식 [cite: 104, 731]
        osm = (2 * na) + (glu / 18) + (bun / 2.8)
        st.metric("계산된 혈장 삼투압", f"{osm:.1f} mOsm/L")
        if osm > 350:
            st.error("🚨 HHS(고삼투압 고혈당 상태) 위험! 수액을 매우 천천히 교정해야 합니다. [cite: 720]")

st.divider()

# --- [3] 영양 공급량 (RER) 계산 ---
st.header("🍴 [Step 2] 영양 요구량 (RER) 계산")
# 기초 대사량 공식 (Standard RER: 70 * BW^0.75)
rer = 70 * (weight ** 0.75)

col3, col4 = st.columns(2)
with col3:
    st.subheader("기초 에너지 요구량")
    st.info(f"이 환자의 **RER (100%): {rer:.1f} kcal/day**")
    rer_target_pct = st.slider("목표 RER 공급 비율 (%)", 33, 100, 33)
    target_kcal = rer * (rer_target_pct / 100)
    st.success(f"**설정된 목표 칼로리: {target_kcal:.1f} kcal/day**")
    st.caption("참고: 거식증 환자는 재급식 증후군 방지를 위해 RER의 1/3부터 시작하는 것이 권장됩니다. ")

st.divider()

# --- [4] 아미노산 & 비경구 영양(PN) 설계 ---
st.header("💉 [Step 3] 아미노산 및 PN(TPN/PPN) 계획")
st.markdown("사용 중인 제품의 농도와 공유해주신 임상 용량 범위를 적용합니다.")

pn_col1, pn_col2 = st.columns(2)

with pn_col1:
    st.subheader("1. 아미노산(AA) 설정")
    # 질환 유무에 따른 보수적 용량 가이드 (이미지 참고)
    if is_complex:
        aa_default, aa_max = 0.5, 1.5
        aa_msg = "CKD/간/심장 질환군 가이드 적용"
    else:
        aa_default, aa_max = 1.0, 2.0
        aa_msg = "일반/중증 환자 가이드 적용"
        
    aa_dose_g_kg = st.number_input(f"AA 용량 (g/kg/day) - {aa_msg}", 
                                   min_value=0.1, max_value=2.5, value=aa_default, step=0.1)
    
    aa_product = st.selectbox("아미노산 제품 선택", 
                               ["신장: 네프리솔 (5.6%)", "고용량: 10% 후라바솔", "간: 후리바솔-헤파 (6.5%)"])
    
    # 농도 매핑
    conc_map = {"신장: 네프리솔 (5.6%)": 5.6, "고용량: 10% 후라바솔": 10.0, "간: 후리바솔-헤파 (6.5%)": 6.5}
    aa_conc = conc_map[aa_product]
    
    total_aa_g = weight * aa_dose_g_kg
    aa_kcal = total_aa_g * 4  # 단백질 4 kcal/g
    aa_ml = (total_aa_g / aa_conc) * 100

with pn_col2:
    st.subheader("2. 비단백 칼로리(NPC) 분배")
    npc_kcal = target_kcal - aa_kcal
    if npc_kcal < 0:
        st.error("목표 칼로리가 아미노산 칼로리보다 낮습니다. RER 비율을 높이거나 AA 용량을 조절하세요.")
        npc_kcal = 0
    
    st.write(f"아미노산 칼로리: {aa_kcal:.1f} kcal")
    st.write(f"남은 칼로리(NPC): {npc_kcal:.1f} kcal")
    
    # 포도당 vs 지질 비율 설정 (예: 50:50)
    glu_ratio = st.slider("포도당(Glucose) 비율 (%)", 0, 100, 50)
    lipid_ratio = 100 - glu_ratio
    
    glu_kcal = npc_kcal * (glu_ratio / 100)
    lipid_kcal = npc_kcal * (lipid_ratio / 100)
    
    # 제품별 볼륨 계산 (표준 농도 가정)
    # Dextrose 50% = 1.7 kcal/mL, Lipid 20% = 2.0 kcal/mL
    glu_ml = glu_kcal / 1.7
    lipid_ml = lipid_kcal / 2.0
    
    st.subheader("📦 최종 PN 조제 가이드")
    st.info(f"""
    - **{aa_product}**: {aa_ml:.1f} mL
    - **Dextrose 50%**: {glu_ml:.1f} mL
    - **Lipid 20%**: {lipid_ml:.1f} mL
    - **총 PN 볼륨**: {aa_ml + glu_ml + lipid_ml:.1f} mL
    """)

st.divider()

# --- [5] 수액 과부하 모니터링 체크리스트 ---
st.header("🚨 수액 과부하(Fluid Overload) 감시 지표")
st.markdown("수액과 PN이 동시 투여될 때 특히 주의가 필요합니다. [cite: 821, 867]")
check_col1, check_col2 = st.columns(2)
with check_col1:
    st.checkbox("체중 10% 이상 증가 [cite: 930]")
    st.checkbox("장액성 비강 분비물 [cite: 884]")
    st.checkbox("결막 부종 (Chemosis) [cite: 884]")
with check_col2:
    st.checkbox("호흡수/노력 증가 (폐부종 징후) [cite: 884]")
    st.checkbox("새로운 심잡음 또는 갤럽음 [cite: 884]")
    st.checkbox("말단 부종 (Paws/Limbs) [cite: 884]")

st.caption("Reference: 2024 AAHA Fluid Therapy Guidelines & User Specified Amino Acid/PN Protocol")
