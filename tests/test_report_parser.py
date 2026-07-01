"""
test_report_parser.py
---------------------
리포트 집계 로직에 대한 단위 테스트.
LiteLLM Proxy 실행 불필요 — 순수 로직만 테스트한다.
"""

import pytest


# ---------------------------------------------------------------------------
# 테스트 대상 함수
# ---------------------------------------------------------------------------

def aggregate_spend_by_user(key_list: list[dict]) -> dict[str, float]:
    """
    키 목록에서 user_id 별로 spend를 합산한다.

    Args:
        key_list: LiteLLM /key/list API 응답 형태의 딕셔너리 리스트.
                  각 항목은 "user_id"와 "spend" 필드를 포함할 수 있다.

    Returns:
        {user_id: total_spend} 형태의 딕셔너리.
    """
    result: dict[str, float] = {}
    for key in key_list:
        user = key.get("user_id", "unknown")
        spend = key.get("spend", 0.0)
        result[user] = result.get(user, 0.0) + spend
    return result


# ---------------------------------------------------------------------------
# 개별 이름 테스트 (명세 요구사항 명시적 충족)
# ---------------------------------------------------------------------------

def test_aggregate_single_user():
    """kim 의 키 하나 → {kim: 1.5}"""
    key_list = [{"user_id": "kim", "spend": 1.5}]
    result = aggregate_spend_by_user(key_list)
    assert result == {"kim": 1.5}


def test_aggregate_multiple_keys_same_user():
    """kim 의 키 두 개 → {kim: 3.0}"""
    key_list = [
        {"user_id": "kim", "spend": 1.5},
        {"user_id": "kim", "spend": 1.5},
    ]
    result = aggregate_spend_by_user(key_list)
    assert result == {"kim": 3.0}


def test_aggregate_multiple_users():
    """kim + lee 키 → {kim: 1.5, lee: 0.5}"""
    key_list = [
        {"user_id": "kim", "spend": 1.5},
        {"user_id": "lee", "spend": 0.5},
    ]
    result = aggregate_spend_by_user(key_list)
    assert result == {"kim": 1.5, "lee": 0.5}


def test_aggregate_empty_list():
    """빈 리스트 → {}"""
    result = aggregate_spend_by_user([])
    assert result == {}


def test_aggregate_zero_spend():
    """spend 필드 없는 키 → {kim: 0.0}"""
    key_list = [{"user_id": "kim"}]
    result = aggregate_spend_by_user(key_list)
    assert result == {"kim": 0.0}


# ---------------------------------------------------------------------------
# Parametrize 테스트
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "key_list, expected",
    [
        # 단일 사용자
        ([{"user_id": "kim", "spend": 1.5}], {"kim": 1.5}),
        # 동일 사용자 복수 키
        (
            [{"user_id": "kim", "spend": 1.5}, {"user_id": "kim", "spend": 1.5}],
            {"kim": 3.0},
        ),
        # 복수 사용자
        (
            [{"user_id": "kim", "spend": 1.5}, {"user_id": "lee", "spend": 0.5}],
            {"kim": 1.5, "lee": 0.5},
        ),
        # 빈 목록
        ([], {}),
        # spend 필드 누락
        ([{"user_id": "kim"}], {"kim": 0.0}),
    ],
    ids=[
        "single_user",
        "multiple_keys_same_user",
        "multiple_users",
        "empty_list",
        "zero_spend",
    ],
)
def test_aggregate_spend_parametrize(key_list, expected):
    assert aggregate_spend_by_user(key_list) == expected


# ---------------------------------------------------------------------------
# 추가 엣지 케이스
# ---------------------------------------------------------------------------

def test_aggregate_missing_user_id():
    """user_id 필드가 없으면 'unknown' 으로 집계된다."""
    key_list = [{"spend": 2.0}, {"spend": 3.0}]
    result = aggregate_spend_by_user(key_list)
    assert result == {"unknown": 5.0}


def test_aggregate_all_three_poc_users():
    """PoC 3인 사용자(kim, lee, park) 전체 집계."""
    key_list = [
        {"user_id": "kim", "spend": 0.05},
        {"user_id": "kim", "spend": 0.03},
        {"user_id": "lee", "spend": 0.01},
        {"user_id": "park", "spend": 0.10},
    ]
    result = aggregate_spend_by_user(key_list)
    assert pytest.approx(result["kim"]) == 0.08
    assert pytest.approx(result["lee"]) == 0.01
    assert pytest.approx(result["park"]) == 0.10


def test_aggregate_float_precision():
    """부동소수점 합산이 근사적으로 정확하다."""
    key_list = [{"user_id": "kim", "spend": 0.1}, {"user_id": "kim", "spend": 0.2}]
    result = aggregate_spend_by_user(key_list)
    assert pytest.approx(result["kim"]) == 0.3
