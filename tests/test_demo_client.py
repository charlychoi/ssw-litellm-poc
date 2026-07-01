"""
test_demo_client.py
-------------------
데모 클라이언트 요청 빌드 로직에 대한 단위 테스트.
외부 API 호출 없음 — 순수 로직만 테스트한다.
"""

import pytest


# ---------------------------------------------------------------------------
# 테스트 대상 함수
# ---------------------------------------------------------------------------

def build_chat_request(model: str, prompt: str, user_id: str) -> dict:
    """
    LiteLLM /v1/chat/completions 엔드포인트용 요청 페이로드를 생성한다.

    Args:
        model:   LiteLLM 모델 alias (예: "ssw-fake")
        prompt:  사용자 입력 텍스트
        user_id: 요청자 식별자 (예: "kim")

    Returns:
        요청 페이로드 딕셔너리.
    """
    return {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "user": user_id,
        "max_tokens": 100,
    }


# ---------------------------------------------------------------------------
# 개별 이름 테스트 (명세 요구사항 명시적 충족)
# ---------------------------------------------------------------------------

def test_basic_request():
    """기본 요청 구조가 올바르게 생성된다."""
    result = build_chat_request(model="ssw-fake", prompt="hello", user_id="kim")

    assert isinstance(result, dict)
    assert "model" in result
    assert "messages" in result
    assert "user" in result
    assert "max_tokens" in result


def test_model_in_request():
    """model 필드가 올바르게 설정된다."""
    result = build_chat_request(model="ssw-fake", prompt="hello", user_id="kim")
    assert result["model"] == "ssw-fake"


def test_messages_format():
    """messages 필드가 role과 content를 포함한 리스트 형태이다."""
    result = build_chat_request(model="ssw-fake", prompt="hello", user_id="kim")

    messages = result["messages"]
    assert isinstance(messages, list)
    assert len(messages) == 1

    msg = messages[0]
    assert "role" in msg
    assert "content" in msg
    assert msg["role"] == "user"
    assert msg["content"] == "hello"


def test_user_field():
    """user 필드가 user_id와 일치한다."""
    result = build_chat_request(model="ssw-fake", prompt="hello", user_id="kim")
    assert result["user"] == "kim"


# ---------------------------------------------------------------------------
# Parametrize 테스트
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "model, prompt, user_id",
    [
        ("ssw-fake", "hello", "kim"),
        ("ssw-dev-sonnet", "Python 코드 작성해줘", "kim"),
        ("ssw-low-cost", "회의록 요약해줘", "lee"),
        ("ssw-expensive", "테스트 쿼리", "park"),
    ],
    ids=["fake_model", "sonnet_model", "low_cost_model", "expensive_model"],
)
def test_build_chat_request_parametrize(model, prompt, user_id):
    """다양한 모델/사용자 조합에서 요청 구조가 올바르다."""
    result = build_chat_request(model=model, prompt=prompt, user_id=user_id)

    assert result["model"] == model
    assert result["user"] == user_id
    assert result["messages"][0]["content"] == prompt
    assert result["messages"][0]["role"] == "user"
    assert result["max_tokens"] == 100


# ---------------------------------------------------------------------------
# 추가 검증 테스트
# ---------------------------------------------------------------------------

def test_max_tokens_is_100():
    """max_tokens 는 항상 100으로 고정된다."""
    result = build_chat_request(model="ssw-fake", prompt="test", user_id="kim")
    assert result["max_tokens"] == 100


def test_messages_has_exactly_one_message():
    """messages 리스트는 정확히 1개의 메시지를 포함한다."""
    result = build_chat_request(model="ssw-fake", prompt="test", user_id="kim")
    assert len(result["messages"]) == 1


def test_prompt_preserved_verbatim():
    """긴 프롬프트도 변형 없이 content 에 그대로 담긴다."""
    long_prompt = "이것은 매우 긴 프롬프트입니다. " * 50
    result = build_chat_request(model="ssw-fake", prompt=long_prompt, user_id="kim")
    assert result["messages"][0]["content"] == long_prompt


def test_all_poc_users():
    """PoC 3인 사용자(kim, lee, park) 모두에 대해 올바른 페이로드가 생성된다."""
    for user in ["kim", "lee", "park"]:
        result = build_chat_request(model="ssw-fake", prompt="test", user_id=user)
        assert result["user"] == user


def test_request_does_not_contain_api_key():
    """요청 페이로드에 API 키가 포함되지 않는다 (키는 헤더로 전달)."""
    result = build_chat_request(model="ssw-fake", prompt="hello", user_id="kim")
    result_str = str(result)
    assert "api_key" not in result_str
    assert "Authorization" not in result_str
    assert "Bearer" not in result_str
