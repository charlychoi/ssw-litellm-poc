"""
test_key_policy.py
------------------
모델 접근 정책 로직에 대한 단위 테스트.
LiteLLM Proxy 실행 불필요 — 순수 로직만 테스트한다.
"""

import pytest


# ---------------------------------------------------------------------------
# 테스트 대상 함수
# ---------------------------------------------------------------------------

def is_model_allowed(model: str, allowed_models: list[str]) -> bool:
    """model이 allowed_models 목록에 있으면 True(접근 허용), 없으면 False(차단)."""
    return model in allowed_models


# ---------------------------------------------------------------------------
# Parametrize 테스트
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "model, allowed_models, expected",
    [
        # 1. 허용된 모델
        ("ssw-dev-sonnet", ["ssw-dev-sonnet", "ssw-fake"], True),
        # 2. 허용 목록에 없는 모델
        ("ssw-expensive", ["ssw-low-cost", "ssw-fake"], False),
        # 3. 허용 목록이 비어 있음
        ("ssw-dev-sonnet", [], False),
        # 4. 관리자 — 고가 모델 포함 전체 허용
        ("ssw-expensive", ["ssw-dev-sonnet", "ssw-dev-gpt", "ssw-expensive"], True),
        # 5. 일반 직원 — 고가 모델 접근 불가
        ("ssw-expensive", ["ssw-low-cost", "ssw-fake", "low-cost"], False),
    ],
    ids=[
        "allowed_model",
        "denied_model",
        "empty_allowed_list",
        "admin_all_models",
        "staff_cant_use_expensive",
    ],
)
def test_key_policy(model: str, allowed_models: list[str], expected: bool):
    assert is_model_allowed(model, allowed_models) == expected


# ---------------------------------------------------------------------------
# 개별 이름 테스트 (명세 요구사항 명시적 충족)
# ---------------------------------------------------------------------------

def test_allowed_model():
    """허용 목록에 있는 모델은 접근이 허용된다."""
    assert is_model_allowed("ssw-dev-sonnet", ["ssw-dev-sonnet", "ssw-fake"]) is True


def test_denied_model():
    """허용 목록에 없는 모델은 차단된다."""
    assert is_model_allowed("ssw-expensive", ["ssw-low-cost", "ssw-fake"]) is False


def test_empty_allowed_list():
    """허용 목록이 비어 있으면 어떤 모델도 접근 불가하다."""
    assert is_model_allowed("ssw-dev-sonnet", []) is False
    assert is_model_allowed("ssw-fake", []) is False


def test_admin_all_models():
    """관리자 키는 고가 모델을 포함한 전체 목록에 접근할 수 있다."""
    admin_models = ["ssw-dev-sonnet", "ssw-dev-gpt", "ssw-expensive"]
    assert is_model_allowed("ssw-expensive", admin_models) is True


def test_staff_cant_use_expensive():
    """일반 직원 키는 고가 모델에 접근할 수 없다."""
    staff_models = ["ssw-low-cost", "ssw-fake", "low-cost"]
    assert is_model_allowed("ssw-expensive", staff_models) is False


# ---------------------------------------------------------------------------
# 추가 엣지 케이스
# ---------------------------------------------------------------------------

def test_model_case_sensitive():
    """모델명 비교는 대소문자를 구분한다."""
    assert is_model_allowed("SSW-FAKE", ["ssw-fake"]) is False
    assert is_model_allowed("ssw-fake", ["ssw-fake"]) is True


def test_ssw_fake_universally_accessible():
    """ssw-fake 모델은 모든 역할의 허용 목록에 포함된다 (PoC 정책)."""
    for allowed in [
        ["ssw-dev-sonnet", "ssw-fake", "ssw-free-test"],
        ["ssw-dev-gpt", "ssw-fake"],
        ["ssw-free-test", "ssw-fake"],
        ["ssw-low-cost", "ssw-fake"],
    ]:
        assert is_model_allowed("ssw-fake", allowed) is True
