import streamlit as st
from openai import OpenAI
import json

# ── 페이지 기본 설정 ─────────────────────────────────────
st.set_page_config(
    page_title="금융 민원 분석기",
    page_icon="🏦",
    layout="centered",
)

# ── API 클라이언트 ────────────────────────────────────────
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# ── 상수 ─────────────────────────────────────────────────
SYSTEM_PROMPT = """
당신은 금융소비자보호 전문가입니다.
고객의 민원 텍스트를 분석하여 반드시 아래 JSON 형식으로만 응답하세요.
JSON 외의 다른 텍스트나 마크다운은 절대 포함하지 마세요.

{
  "category": "수수료 | 불완전판매 | 금리 | 대출 | 보험 | 카드 | 기타 중 하나",
  "category_reason": "해당 유형으로 분류한 이유 (1~2줄)",
  "summary": "민원의 핵심 쟁점 요약 (2~3줄)",
  "response": "고객에게 전달할 1차 응대용 공식 문구. 아래 구조로 작성하세요:\n1) 고객 불편에 대한 진심 어린 사과\n2) 민원 핵심 내용 확인 및 공감\n3) 구체적인 처리 절차 또는 조치 안내\n4) 추가 문의 채널 안내 (고객센터 등)\n정중하고 공식적인 어투, 7~10줄"
}

[민원 유형 분류 기준]
- 수수료: 이체/ATM/펀드 수수료 관련 불만
- 불완전판매: 상품 설명 부족, 리스크 미고지
- 금리: 예금·대출 금리 관련 불만
- 대출: 대출 심사, 한도, 조건 관련
- 보험: 보험료, 보험금 지급 관련
- 카드: 카드 발급, 한도, 청구 관련
- 기타: 위 항목에 해당하지 않는 경우

반드시 JSON만 출력하세요. 설명, 마크다운, ```json 코드블록 절대 금지.
"""

CATEGORY_EMOJI = {
    "수수료": "💳",
    "불완전판매": "⚠️",
    "금리": "📈",
    "대출": "🏦",
    "보험": "🛡️",
    "카드": "💳",
    "기타": "📋",
}

CATEGORY_COLOR = {
    "수수료": "#4A90D9",
    "불완전판매": "#E05C5C",
    "금리": "#5BB85D",
    "대출": "#F0A500",
    "보험": "#8B5CF6",
    "카드": "#3B82F6",
    "기타": "#6B7280",
}

SAMPLE_COMPLAINTS = [
    "펀드 가입 시 직원이 원금 보장된다고 했으나, 실제로는 원금 손실 가능성이 있는 상품이었습니다.",
    "타 은행 대비 금리가 너무 낮아 손해를 보고 있습니다. 금리 조정을 요청합니다.",
    "ATM 수수료가 갑자기 인상되었는데 사전 공지를 받지 못했습니다.",
]


# ── 분석 함수 ─────────────────────────────────────────────
def analyze_complaint(text: str) -> dict:
    response = client.chat.completions.create(
        model="gpt-5.5",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"[민원 내용]\n{text}"},
        ],
        max_completion_tokens=1500,
    )
    raw = response.choices[0].message.content.strip()
    return json.loads(raw)


# ── UI ───────────────────────────────────────────────────
st.title("🏦 금융 소비자 민원 분석기")
st.caption("민원 내용을 입력하면 GPT가 유형 분류 · 쟁점 요약 · 1차 응대 문구를 자동 생성합니다.")
st.divider()

# 예시 민원 선택
with st.expander("예시 민원 불러오기"):
    for i, sample in enumerate(SAMPLE_COMPLAINTS):
        if st.button(f"예시 {i+1}", key=f"sample_{i}"):
            st.session_state["complaint_input"] = sample

# 민원 입력
complaint = st.text_area(
    "민원 내용 입력",
    value=st.session_state.get("complaint_input", ""),
    placeholder="고객 민원 내용을 여기에 입력하세요...",
    height=160,
    key="complaint_input",
)

col1, col2 = st.columns([3, 1])
with col1:
    analyze_btn = st.button("분석 시작", type="primary", use_container_width=True)
with col2:
    clear_btn = st.button("초기화", use_container_width=True)

if clear_btn:
    st.session_state["complaint_input"] = ""
    st.rerun()

# 분석 실행
if analyze_btn:
    if not complaint.strip():
        st.warning("민원 내용을 입력해주세요.")
    else:
        with st.spinner("GPT가 민원을 분석 중입니다..."):
            try:
                result = analyze_complaint(complaint)

                st.divider()
                st.subheader("분석 결과")

                # 민원 유형
                cat = result.get("category", "기타")
                emoji = CATEGORY_EMOJI.get(cat, "📋")
                color = CATEGORY_COLOR.get(cat, "#6B7280")

                st.markdown(
                    f"""
                    <div style='background:{color}22; border-left:4px solid {color};
                    padding:12px 16px; border-radius:6px; margin-bottom:8px;'>
                        <strong style='color:{color}; font-size:18px;'>{emoji} 민원 유형: {cat}</strong><br>
                        <span style='color:#555; font-size:14px;'>{result.get('category_reason', '')}</span>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                # 핵심 쟁점 요약
                st.markdown("**📝 핵심 쟁점 요약**")
                st.info(result.get("summary", ""))

                # 1차 응대 문구
                st.markdown("**💬 1차 응대 문구**")
                st.success(result.get("response", ""))

                # 복사용 텍스트
                with st.expander("응대 문구 전체 복사"):
                    st.code(result.get("response", ""), language=None)

            except json.JSONDecodeError:
                st.error("GPT 응답 파싱에 실패했습니다. 다시 시도해주세요.")
            except Exception as e:
                st.error(f"오류가 발생했습니다: {e}")

# 하단 안내
st.divider()
st.caption("⚠️ 본 서비스는 1차 응대 보조 도구입니다. 최종 응대 문구는 담당자가 검토 후 사용하세요.")