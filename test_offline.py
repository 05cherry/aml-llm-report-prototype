"""오프라인 테스트 (실 API 호출/키 불필요).

추가 의존성 없이 plain assert로 구성한다. 저장소 루트에서 실행:
    .venv/Scripts/python.exe test_offline.py

검증 범위:
- derive_risk: none / medium / high(두 분기: S4 단독, 신호 2개 이상)
- 5개 계정 구조 동일성(4개 섹션) — 완료 기준 #4
- 정상 계정 "특이사항 없음" 표기 — 완료 기준 #3
- 시스템 프롬프트 무-ID 불변식(ACC-/T- 미포함)
- 신호 정의 문서 UTF-8 정상 로드(한글 깨짐 없음)
"""

import sys

from src.signals import derive_risk
from src.renderer import render
from src.reviewer import build_system_prompt

_failures = []


def check(name, cond):
    print(("  PASS  " if cond else "  FAIL  ") + name)
    if not cond:
        _failures.append(name)


# --- derive_risk -----------------------------------------------------------
def sig(sid):
    return {"signal_id": sid, "signal_name": sid, "evidence": "e", "related_transaction_ids": []}


check("derive_risk none: 빈 신호", derive_risk([]) == "none")
check("derive_risk medium: 단일 S1", derive_risk([sig("S1")]) == "medium")
check("derive_risk medium: 단일 S5", derive_risk([sig("S5")]) == "medium")
check("derive_risk high-A: S4 단독", derive_risk([sig("S4")]) == "high")
check("derive_risk high-A: S3+S4", derive_risk([sig("S3"), sig("S4")]) == "high")
check("derive_risk high-B: S1+S2(2개)", derive_risk([sig("S1"), sig("S2")]) == "high")
check("derive_risk high-B: S3+S5(2개)", derive_risk([sig("S3"), sig("S5")]) == "high")


# --- 5개 계정 구조 동일성 (완료 기준 #4) -----------------------------------
EXPECTED_SECTIONS = ["### 의심 신호 후보", "### 탐지 근거", "### 추가 확인 항목", "### 위험도"]


def review(account_id, signals):
    return {
        "account_id": account_id,
        "risk_level": "ignored",  # 모델 값은 렌더링에서 무시됨
        "summary": "요약 문장",
        "signals": signals,
        "follow_up_actions": ["추가 확인 항목 1"] if signals else [],
    }


cases = [
    ("ACC-N", []),                                  # 신호 없음
    ("ACC-1", [sig("S1")]),                          # 단일
    ("ACC-2", [sig("S5")]),                          # 단일
    ("ACC-3", [sig("S1"), sig("S2")]),               # 다중
    ("ACC-4", [sig("S4")]),                          # S4 포함
]
for aid, signals in cases:
    md = render(review(aid, signals))
    headers = [ln for ln in md.splitlines() if ln.startswith("### ")]
    check(f"구조 동일성[{aid}]: 4개 섹션/순서 일치", headers == EXPECTED_SECTIONS)


# --- 정상 계정 "특이사항 없음" (완료 기준 #3) ------------------------------
normal_md = render(review("ACC-E", []))
check("정상 계정: '특이사항 없음' 표기", "특이사항 없음" in normal_md)
check("정상 계정: 위험도 낮음", "낮음" in normal_md)


# --- 시스템 프롬프트 무-ID 불변식 ------------------------------------------
system_prompt = build_system_prompt()
check("system prompt: 계정 ID(ACC-) 미포함", "ACC-" not in system_prompt)
check("system prompt: 거래 ID(T-) 미포함", "T-" not in system_prompt)


# --- 문서 UTF-8 정상 로드 --------------------------------------------------
check("aml-signals.md 한글 정상 로드", "의심 신호" in system_prompt)


# --- 결과 ------------------------------------------------------------------
if _failures:
    print(f"\n실패 {len(_failures)}건: {_failures}")
    sys.exit(1)
print("\n모든 오프라인 테스트 통과")
sys.exit(0)
