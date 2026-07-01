"""
test_budget_policy.py
---------------------
예산 정책 로직에 대한 단위 테스트.
LiteLLM Proxy 실행 불필요 — 순수 로직만 테스트한다.
"""

import pytest


# ---------------------------------------------------------------------------
# 테스트 대상 함수 (프로덕션 코드와 동일하게 유지)
# ---------------------------------------------------------------------------

def is_budget_allowed(current_spend: float, max_budget: float) -> bool:
    """현재 지출이 max_budget 미만이면 True(허용), 이상이면 False(차단)."""
    return current_spend < max_budget


# ---------------------------------------------------------------------------
# Parametrize 테스트
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "current_spend, max_budget, expected",
    [
        # 1. 예산 내 사용 → 허용
        (0.5, 1.0, True),
        # 2. 예산 초과 → 차단
        (1.1, 1.0, False),
        # 3. 예산 정확히 동일 → 차단 (strict <)
        (1.0, 1.0, False),
        # 4. max_budget=0 → 모든 지출 차단
        (0.001, 0.0, False),
    ],
    ids=[
        "budget_within_limit",
        "budget_exceeded",
        "budget_at_limit",
        "budget_zero_limit",
    ],
)
def test_budget_policy(current_spend: float, max_budget: float, expected: bool):
    assert is_budget_allowed(current_spend, max_budget) == expected


# ---------------------------------------------------------------------------
# 개별 이름 테스트 (명세 요구사항 명시적 충족)
# ---------------------------------------------------------------------------

def test_budget_within_limit():
    """지출이 한도 미만이면 허용된다."""
    assert is_budget_allowed(0.5, 1.0) is True


def test_budget_exceeded():
    """지출이 한도를 초과하면 차단된다."""
    assert is_budget_allowed(1.1, 1.0) is False


def test_budget_at_limit():
    """지출이 한도와 정확히 같으면 차단된다 (strict < 정책)."""
    assert is_budget_allowed(1.0, 1.0) is False


def test_budget_zero_limit():
    """max_budget=0 이면 아무리 작은 지출도 차단된다."""
    assert is_budget_allowed(0.001, 0.0) is False


# ---------------------------------------------------------------------------
# 엣지 케이스 추가 테스트
# ---------------------------------------------------------------------------

def test_budget_zero_spend_nonzero_limit():
    """지출이 0이고 한도가 양수이면 허용된다."""
    assert is_budget_allowed(0.0, 1.0) is True


def test_budget_large_values():
    """큰 값에서도 정책이 정상 동작한다."""
    assert is_budget_allowed(999.99, 1000.0) is True
    assert is_budget_allowed(1000.0, 1000.0) is False
    assert is_budget_allowed(1000.01, 1000.0) is False
