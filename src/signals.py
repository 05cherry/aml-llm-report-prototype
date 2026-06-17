"""위험도 판정 로직.

위험도 산정 규칙은 docs/aml-signals.md의 "위험도 산정 (예시 규칙)" 표를 그대로
옮긴 것이다. 그 문서가 단일 진실 공급원(SSoT)이다. 규칙이 바뀌면 문서를 먼저
고친 뒤 이 함수를 맞춘다. (CLAUDE.md 도메인 규칙)

  - High   : 고위험 주소 연관(S4) 발생, 또는 신호 2개 이상 동시 충족
  - Medium : 단일 신호(S1·S2·S3·S5 중 하나) 충족
  - None   : 충족 신호 없음 → "특이사항 없음"
"""


def derive_risk(signals):
    """탐지된 신호 목록으로부터 위험도(none/medium/high)를 파생한다.

    모델이 제출한 risk_level을 신뢰하지 않고, 신호 집합에서 문서 규칙으로
    다시 산정한다(렌더링 시 이 값이 권위).
    """
    ids = {s.get("signal_id") for s in signals}
    if not ids:
        return "none"
    if "S4" in ids or len(ids) >= 2:
        return "high"
    return "medium"
