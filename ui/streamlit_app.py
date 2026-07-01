"""
상상우리 LiteLLM AI 비용 거버넌스 PoC — Streamlit UI
LiteLLM version: 1.83.7
"""

import json
import os
from pathlib import Path

import requests
import streamlit as st
from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# 환경변수 로드
# ---------------------------------------------------------------------------
# .env 파일을 프로젝트 루트에서 찾는다
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(_PROJECT_ROOT / ".env")

LITELLM_BASE_URL = os.getenv("LITELLM_BASE_URL", "http://localhost:4000")
LITELLM_MASTER_KEY = os.getenv("LITELLM_MASTER_KEY", "")

# ---------------------------------------------------------------------------
# 정책 상수 — PoC 하드코딩
# ---------------------------------------------------------------------------
KEY_MAP: dict[tuple[str, str], dict] = {
    ("kim", "claude-code"): {
        "alias": "dev-kim-claude",
        "models": ["ssw-dev-sonnet", "ssw-fake", "ssw-free-test"],
    },
    ("kim", "codex-cli"): {
        "alias": "dev-kim-codex",
        "models": ["ssw-dev-gpt", "ssw-fake"],
    },
    ("kim", "gemini-cli"): {
        "alias": "dev-kim-gemini",
        "models": ["ssw-free-test", "ssw-fake"],
    },
    ("lee", "chat"): {
        "alias": "staff-lee-chat",
        "models": ["ssw-low-cost", "ssw-fake"],
    },
    ("park", "admin-api"): {
        "alias": "admin-park-test",
        "models": ["ssw-dev-sonnet", "ssw-dev-gpt", "ssw-free-test", "ssw-expensive", "ssw-fake"],
    },
}

USER_TOOLS: dict[str, list[str]] = {
    "kim": ["claude-code", "codex-cli", "gemini-cli"],
    "lee": ["chat"],
    "park": ["admin-api"],
}

GENERATED_KEYS_PATH = _PROJECT_ROOT / "docs" / "generated_keys.json"

# ---------------------------------------------------------------------------
# 헬퍼 함수
# ---------------------------------------------------------------------------

def load_generated_keys() -> dict[str, str] | None:
    """docs/generated_keys.json 에서 alias → key 매핑을 로드한다."""
    if not GENERATED_KEYS_PATH.exists():
        return None
    try:
        with open(GENERATED_KEYS_PATH, encoding="utf-8") as f:
            data = json.load(f)
        # 지원 포맷: {"dev-kim-claude": "sk-...", ...}  또는  [{"alias": ..., "key": ...}, ...]
        if isinstance(data, dict):
            return data
        if isinstance(data, list):
            return {item["alias"]: item["key"] for item in data if "alias" in item and "key" in item}
    except Exception as exc:
        st.warning(f"generated_keys.json 파싱 오류: {exc}")
    return None


def get_virtual_key(alias: str, keys_map: dict[str, str] | None) -> str | None:
    """alias 에 해당하는 실제 sk- 키를 반환한다."""
    if keys_map is None:
        return None
    return keys_map.get(alias)


def proxy_headers(key: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}


def admin_headers() -> dict[str, str]:
    return {"Authorization": f"Bearer {LITELLM_MASTER_KEY}", "Content-Type": "application/json"}


def call_chat_completion(model: str, prompt: str, user_id: str, api_key: str) -> tuple[dict | None, float | None, str | None]:
    """
    LiteLLM Proxy 에 chat completion 요청을 보낸다.
    Returns: (response_json, cost, error_message)
    """
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "user": user_id,
        "max_tokens": 100,
    }
    try:
        resp = requests.post(
            f"{LITELLM_BASE_URL}/v1/chat/completions",
            json=payload,
            headers=proxy_headers(api_key),
            timeout=30,
        )
        cost: float | None = None
        raw_cost = resp.headers.get("x-litellm-response-cost")
        if raw_cost:
            try:
                cost = float(raw_cost)
            except ValueError:
                pass

        if resp.ok:
            return resp.json(), cost, None
        else:
            try:
                err_body = resp.json()
                detail = err_body.get("error", {}).get("message", resp.text)
            except Exception:
                detail = resp.text
            return None, cost, f"[{resp.status_code}] {detail}"
    except requests.exceptions.ConnectionError:
        return None, None, "LiteLLM Proxy가 실행되지 않고 있습니다. README의 3단계를 확인하세요."
    except Exception as exc:
        return None, None, str(exc)


def fetch_key_list() -> list[dict] | None:
    """GET /key/list — 관리자 키 목록 조회"""
    try:
        resp = requests.get(
            f"{LITELLM_BASE_URL}/key/list",
            headers=admin_headers(),
            timeout=10,
        )
        if resp.ok:
            data = resp.json()
            # 반환 구조: {"keys": [...]} 또는 직접 리스트
            if isinstance(data, list):
                return data
            return data.get("keys", data.get("data", []))
        st.error(f"키 목록 조회 실패: [{resp.status_code}] {resp.text}")
    except requests.exceptions.ConnectionError:
        st.error("LiteLLM Proxy가 실행되지 않고 있습니다. README의 3단계를 확인하세요.")
    except Exception as exc:
        st.error(f"키 목록 조회 오류: {exc}")
    return None


def fetch_global_spend() -> dict | None:
    """GET /global/spend/keys — 전체 사용량 요약"""
    try:
        resp = requests.get(
            f"{LITELLM_BASE_URL}/global/spend/keys",
            headers=admin_headers(),
            timeout=10,
        )
        if resp.ok:
            return resp.json()
        st.error(f"사용량 조회 실패: [{resp.status_code}] {resp.text}")
    except requests.exceptions.ConnectionError:
        st.error("LiteLLM Proxy가 실행되지 않고 있습니다. README의 3단계를 확인하세요.")
    except Exception as exc:
        st.error(f"사용량 조회 오류: {exc}")
    return None


# ---------------------------------------------------------------------------
# 페이지 설정
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="상상우리 LiteLLM 거버넌스 PoC",
    page_icon="🛡️",
    layout="wide",
)

st.title("🛡️ 상상우리 LiteLLM AI 비용 거버넌스 PoC")
st.caption(f"LiteLLM Proxy: `{LITELLM_BASE_URL}` | LiteLLM v1.83.7")

# ---------------------------------------------------------------------------
# 가상키 로드 (공통)
# ---------------------------------------------------------------------------
generated_keys = load_generated_keys()
keys_missing = generated_keys is None

# ---------------------------------------------------------------------------
# 탭 구성
# ---------------------------------------------------------------------------
tab_user, tab_admin = st.tabs(["🧑‍💻 사용자 테스트", "🔑 관리자 통제"])

# ===========================================================================
# TAB 1: 사용자 테스트
# ===========================================================================
with tab_user:
    st.header("사용자 테스트 UI")

    if keys_missing:
        st.warning(
            "가상키 미발급 — `scripts/20_seed_keys.py` 먼저 실행하세요\n\n"
            "```bash\npython scripts/20_seed_keys.py\n```"
        )

    col_left, col_right = st.columns([1, 2])

    with col_left:
        st.subheader("요청 설정")

        selected_user = st.selectbox("사용자 선택", ["kim", "lee", "park"], key="user_sel")
        available_tools = USER_TOOLS.get(selected_user, [])
        selected_tool = st.selectbox("도구 선택", available_tools, key="tool_sel")

        key_info = KEY_MAP.get((selected_user, selected_tool), {})
        available_models = key_info.get("models", [])
        selected_model = st.selectbox("모델 선택", available_models, key="model_sel")

        task_type = st.selectbox(
            "업무유형", ["coding", "document", "summary", "general"], key="task_sel"
        )

        default_prompts = {
            "coding": "Python으로 피보나치 수열을 출력하는 함수를 작성해줘.",
            "document": "AI 거버넌스의 중요성에 대해 한 문단으로 요약해줘.",
            "summary": "다음 회의록을 요약해줘: 오늘 회의에서는 AI 비용 절감 방안을 논의했습니다.",
            "general": "안녕하세요! 오늘 날씨 어때요?",
        }
        user_prompt = st.text_area(
            "프롬프트 입력",
            value=default_prompts.get(task_type, ""),
            height=120,
            key="prompt_input",
        )

        send_disabled = keys_missing
        send_btn = st.button("📤 Send", disabled=send_disabled, type="primary")

    with col_right:
        st.subheader("응답 결과")

        if send_btn:
            alias = key_info.get("alias", "")
            api_key = get_virtual_key(alias, generated_keys)

            if not api_key:
                st.error(f"'{alias}' 키를 찾을 수 없습니다. generated_keys.json 을 확인하세요.")
            elif not user_prompt.strip():
                st.warning("프롬프트를 입력해주세요.")
            else:
                with st.spinner(f"{selected_model} 모델에 요청 중..."):
                    response, cost, error = call_chat_completion(
                        model=selected_model,
                        prompt=user_prompt,
                        user_id=selected_user,
                        api_key=api_key,
                    )

                if error:
                    st.error(f"❌ 차단 / 오류\n\n{error}")

                    # 차단 이유 분류
                    err_lower = error.lower()
                    if "budget" in err_lower or "limit" in err_lower:
                        st.warning("차단 이유: 예산 초과 (Budget Exceeded)")
                    elif "model" in err_lower or "not allowed" in err_lower or "access" in err_lower:
                        st.warning("차단 이유: 비허용 모델 접근 (Model Not Allowed)")
                    elif "proxy가 실행" in error:
                        st.info("LiteLLM Proxy가 실행되지 않고 있습니다. README의 3단계를 확인하세요.")
                    else:
                        st.warning("차단 이유: 기타 정책 위반")
                else:
                    st.success("✅ 허용")

                    # 응답 텍스트 추출
                    try:
                        answer = response["choices"][0]["message"]["content"]
                        st.markdown("**응답:**")
                        st.write(answer)
                    except (KeyError, IndexError, TypeError):
                        st.json(response)

                    # 비용 표시
                    if cost is not None:
                        st.metric("예상 비용", f"${cost:.6f}")
                    else:
                        st.caption("비용 정보 없음 (x-litellm-response-cost 헤더 미제공)")

                # 공통 메타 정보
                with st.expander("요청 메타정보"):
                    st.json({
                        "user": selected_user,
                        "tool": selected_tool,
                        "alias": alias,
                        "model": selected_model,
                        "task_type": task_type,
                        "proxy_url": LITELLM_BASE_URL,
                    })
        else:
            st.info("왼쪽에서 설정 후 Send 버튼을 누르세요.")

# ===========================================================================
# TAB 2: 관리자 통제
# ===========================================================================
with tab_admin:
    st.header("관리자 통제 대시보드")

    if not LITELLM_MASTER_KEY:
        st.error("LITELLM_MASTER_KEY 환경변수가 설정되지 않았습니다. .env 파일을 확인하세요.")

    # -----------------------------------------------------------------------
    # Section A: 가상키 현황
    # -----------------------------------------------------------------------
    st.subheader("A. 가상키 현황")

    with st.spinner("키 목록 조회 중..."):
        key_list = fetch_key_list()

    if key_list is not None:
        if key_list:
            rows = []
            for k in key_list:
                max_budget = k.get("max_budget")
                spend = k.get("spend", 0.0) or 0.0
                remaining = (max_budget - spend) if max_budget is not None else None
                rows.append({
                    "alias": k.get("key_alias") or k.get("alias", "-"),
                    "user_id": k.get("user_id", "-"),
                    "models": ", ".join(k.get("models") or []) or "전체",
                    "max_budget ($)": f"{max_budget:.4f}" if max_budget is not None else "무제한",
                    "spent ($)": f"{spend:.6f}",
                    "remaining ($)": f"{remaining:.4f}" if remaining is not None else "-",
                    "status": "활성" if not k.get("blocked") else "차단",
                })
            st.dataframe(rows, use_container_width=True)
        else:
            st.info("등록된 가상키가 없습니다. `scripts/20_seed_keys.py`를 실행하세요.")
    else:
        st.warning("키 목록을 불러오지 못했습니다.")

    st.divider()

    # -----------------------------------------------------------------------
    # Section B: 사용량 요약
    # -----------------------------------------------------------------------
    st.subheader("B. 사용량 요약")

    with st.spinner("사용량 조회 중..."):
        spend_data = fetch_global_spend()

    if spend_data is not None:
        # 구조가 리스트인 경우 vs 딕셔너리인 경우 모두 처리
        items = spend_data if isinstance(spend_data, list) else spend_data.get("data", [spend_data])

        total_calls = sum(int(i.get("total_count", 0) or 0) for i in items if isinstance(i, dict))
        total_cost = sum(float(i.get("total_cost", 0.0) or 0.0) for i in items if isinstance(i, dict))

        col1, col2, col3 = st.columns(3)
        col1.metric("총 호출 수", f"{total_calls:,}")
        col2.metric("총 비용 (USD)", f"${total_cost:.4f}")
        col3.metric("활성 키 수", len(items))

        if items:
            st.markdown("**키별 사용량**")
            table_rows = []
            for i in items:
                if isinstance(i, dict):
                    table_rows.append({
                        "key / alias": i.get("api_key") or i.get("key_alias", "-"),
                        "calls": i.get("total_count", 0),
                        "cost ($)": f"{float(i.get('total_cost', 0.0) or 0.0):.6f}",
                    })
            if table_rows:
                st.dataframe(table_rows, use_container_width=True)
    else:
        st.warning("사용량 데이터를 불러오지 못했습니다.")

    st.divider()

    # -----------------------------------------------------------------------
    # Section C: 차단 이벤트
    # -----------------------------------------------------------------------
    st.subheader("C. 차단 이벤트")
    st.info(
        "LiteLLM에는 별도 차단 이벤트 API가 없습니다. "
        "아래는 spend 로그에서 파악된 오류 이벤트 플레이스홀더입니다.\n\n"
        "실제 운영 환경에서는 LiteLLM Proxy 로그(litellm.log)를 파싱하거나 "
        "Prometheus/Grafana 연동을 권장합니다."
    )
    placeholder_blocks = [
        {
            "timestamp": "2025-07-01 09:12:33",
            "user": "lee",
            "key_alias": "staff-lee-chat",
            "model_requested": "ssw-expensive",
            "reason": "Model not in allowed list",
            "status": "BLOCKED",
        },
        {
            "timestamp": "2025-07-01 10:45:07",
            "user": "kim",
            "key_alias": "dev-kim-claude",
            "model_requested": "ssw-dev-sonnet",
            "reason": "Budget exceeded ($0.01 limit)",
            "status": "BLOCKED",
        },
    ]
    st.dataframe(placeholder_blocks, use_container_width=True)

    st.divider()

    # -----------------------------------------------------------------------
    # Section D: 데모 버튼
    # -----------------------------------------------------------------------
    st.subheader("D. 데모 버튼")

    demo_col1, demo_col2, demo_col3 = st.columns(3)

    with demo_col1:
        if st.button("✅ 정상 호출 테스트", help="ssw-fake 모델을 dev-kim-claude 키로 호출"):
            if keys_missing:
                st.warning("가상키가 발급되지 않았습니다.")
            else:
                demo_key = get_virtual_key("dev-kim-claude", generated_keys)
                if not demo_key:
                    st.error("dev-kim-claude 키를 찾을 수 없습니다.")
                else:
                    with st.spinner("정상 호출 테스트 중..."):
                        resp, cost, err = call_chat_completion(
                            model="ssw-fake",
                            prompt="Hello, this is a governance PoC test.",
                            user_id="kim",
                            api_key=demo_key,
                        )
                    if err:
                        st.error(f"호출 실패: {err}")
                    else:
                        st.success("정상 호출 성공!")
                        try:
                            st.write(resp["choices"][0]["message"]["content"])
                        except Exception:
                            st.json(resp)
                        if cost is not None:
                            st.metric("비용", f"${cost:.6f}")

    with demo_col2:
        if st.button("❌ 비허용 모델 테스트", help="ssw-expensive 모델을 staff-lee-chat 키로 시도"):
            if keys_missing:
                st.warning("가상키가 발급되지 않았습니다.")
            else:
                demo_key = get_virtual_key("staff-lee-chat", generated_keys)
                if not demo_key:
                    st.error("staff-lee-chat 키를 찾을 수 없습니다.")
                else:
                    with st.spinner("비허용 모델 호출 시도 중..."):
                        resp, cost, err = call_chat_completion(
                            model="ssw-expensive",
                            prompt="Can I use this expensive model?",
                            user_id="lee",
                            api_key=demo_key,
                        )
                    if err:
                        st.error(f"❌ 차단됨 (예상된 결과): {err}")
                    else:
                        st.warning("호출이 허용되었습니다. 모델 제한 정책을 확인하세요.")
                        st.json(resp)

    with demo_col3:
        if st.button("🔄 리포트 새로고침"):
            st.rerun()
