import streamlit as st

# 페이지 설정
st.set_page_config(page_title="수의료 통합 수액 & 영양 계산기", layout="wide")

st.title("🐾 2024 AAHA 수액 & 영양 통합 계산기 (v8.0)")
st.markdown("본 도구는 **2024 AAHA 가이드라인**과 병원 내 **조제 실무(K/iCa/AA)**를 완벽히 통합한 최종 버전입니다.")

# --- [1] 환자 정보 및 수액백 설정 (모바일 최적화 상단 배치) ---
st.header("1. 환자 정보 및 수액백 설정")
row1_col1, row1_col2, row1_col3 = st.columns(3)

with row1_col1:
    species = st.selectbox("품종", ["개 (Dog)", "고양이 (Cat)"])
    weight = st.number_input("체중 (kg)", min_value=0.1, value=5.0, step=0.1)

with row1_col2:
    # 수액백 규격: 1000, 500, 100, 50, 30 mL
    bag_size = st.selectbox("수액백 규격 선택 (mL)", [1000, 500, 100, 50, 30])
    dehydration = st.slider("탈수 정도 (%)", 0, 15, 0)

with row1_col3:
    has_heart = st.checkbox("심장병 (수액 50% 제한)")
    has_ckd = st.checkbox("만성 신부전 (Cl 제한)")
    has_liver = st.checkbox("간질환 (AA 선택 주의)")

st.divider()

# --- [2] 전해질 및 검사 수치 입력 ---
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
    st.caption("P는 모니터링용으로 활용됩니다.")

# --- 계산 로직 시작 ---
# 1. 수액량 계산
maint_vol = weight * 50 * (0.5 if has_heart else 1.0)
deficit_vol = weight * (dehydration / 100) * 1000
total_fluid = maint_vol + deficit_vol
hourly_rate = total_fluid / 24

# 2. 전해질 분석 알림 (K, Cl, iCa)
notices = []

# KCl 보정 (2 mEq/mL 기준)
if k_val < 3.5 and hourly_rate > 0:
    if k_val < 2.0: k_limit = 0.5
    elif k_val < 2.5: k_limit = 0.3
    elif k_val < 3.0: k_limit = 0.2
    else: k_limit = 0.1
    k_meq_for_bag = (k_limit * weight / hourly_rate) * bag_size
    k_ml_for_bag = k_meq_for_bag / 2
    notices.append(f"⚠️ **저칼륨혈증**: {bag_size}mL 백에 **KCl {k_ml_for_bag:.1f} mL** 혼합 ({k_limit} mEq/kg/hr 기준)")

# iCa 보정 (10% Ca Gluconate 기준)
if ica < 1.1 and ica > 0:
    ca_bolus = (weight * 0.5, weight * 1.5)
    ca_cri = (weight * 0.27, weight * 1.07)
    notices.append(f"🚨 **저칼슘혈증**: 10% Ca Gluconate **Bolus {ca_bolus[0]:.1f}~{ca_bolus[1]:.1f} mL** (20분간 서서히 IV)")
    notices.append(f"🏥 **CRI**: 10% Ca Gluconate **{ca_cri[0]:.1f}~{ca_cri[1]:.1f} mL/hr** 투여 권장")

# 수액 종류 추천
fluid_type = "완충 결정질액 (Hartmann액 또는 Plasmasol)"
if cl > 120 or has_ckd:
    fluid_type = "Hartmann/Plasmasol (0.9% NaCl 지양)"

# 결과 출력
res_col1, res_col2 = st.columns(2)
with res_col1:
    st.subheader("📊 수액 처방 결과")
    st.success(f"**총 수액량: {total_fluid:.1f} mL/day**")
    st.metric(f"{bag_size}mL 백 기준 속도", f"{hourly_rate:.1f} mL/hr")
    st.write(f"추천 수액: **{fluid_type}**")

with res_col2:
    st.subheader("📢 임상 정밀 리포트")
    for n in notices: st.warning(n)
    if na > 0:
        osm = (2 * na) + (glu / 18) + (bun / 2.8)
        st.write(f"계산된 유효 삼투압: **{osm:.1f} mOsm/L**")
        if osm > 350: st.error("🚨 HHS 위험: 매우 신중한 속도 조절 필요")

st.divider()

# --- [3] 아미노산 및 영양(PN) 설계 ---
st.header("3. 아미노산 및 비경구 영양(PN) 설계")
rer = 70 * (weight ** 0.75)
target_kcal = rer * (st.slider("목표 RER 비율 (%)", 33, 100, 33) / 100)

pn_col1, pn_col2 = st.columns(2)
with pn_col1:
    st.subheader("아미노산(AA) 설정")
    aa_start = 0.5 if (has_heart or has_ckd or has_liver) else 1.0
    aa_dose = st.number_input("AA 용량 (g/kg/day)", value=aa_start, step=0.1)
    aa_prod = st.selectbox("제품 선택", ["네프리솔 (5.6% - 신장)", "10% 후라바솔 (고용량)", "후리바솔-헤파 (6.5% - 간)"])
    
    conc_map = {"네프리솔 (5.6% - 신장)": 5.6, "10% 후라바솔 (고용량)": 10.0, "후리바솔-헤파 (6.5% - 간)": 6.5}
    aa_ml_val = (weight * aa_dose / conc_map[aa_prod]) * 100
    st.info(f"**{aa_prod} 필요량: {aa_ml_val:.1f} mL/day**")

with pn_col2:
    st.subheader("비단백 칼로리(NPC) 구성")
    aa_kcal = (weight * aa_dose) * 4
    npc_kcal = max(0.0, target_kcal - aa_kcal)
    glu_ratio = st.slider("포도당(Dextrose) 비중 (%)", 0, 100, 50)
    
    glu_ml = (npc_kcal * (glu_ratio / 100)) / 1.7
    lip_ml = (npc_kcal * ((100 - glu_ratio) / 100)) / 2.0
    st.info(f"**Dex 50%**: {glu_ml:.1f} mL | **Lipid 20%**: {lip_ml:.1f} mL")

st.divider()

# --- [4] 모니터링 ---
st.header("🚨 수액 과부하 감시")
c1, c2, c3 = st.columns(3)
c1.checkbox("체중 증가 (전일 대비 >10%)")
c2.checkbox("호흡수 및 노력 증가")
c3.checkbox("비강 분비물 또는 결막 부종")

st.caption("Reference: 2024 AAHA Guidelines & 10% Ca Gluconate & 2 mEq/mL KCl Protocol")

