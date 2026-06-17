"""검토 결과(dict) → 계정별 Markdown 리포트.

모든 계정이 동일한 4개 섹션 구조를 갖는다:
의심 신호 후보 / 탐지 근거 / 추가 확인 항목 / 위험도.
"""

from .signals import derive_risk

_RISK_KR = {
    "none": "낮음 (특이사항 없음)",
    "medium": "중간",
    "high": "높음",
}


def render(review):
    """검토 결과 dict 하나를 4개 섹션의 Markdown 블록으로 렌더링한다.

    위험도는 모델의 risk_level이 아니라 derive_risk(signals)로 파생한 값을 쓴다.
    (문서 기준 파생값이 권위. 충돌 시 파생값이 조용히 우선)
    """
    account_id = review.get("account_id", "?")
    signals = review.get("signals") or []
    summary = (review.get("summary") or "").strip()
    follow_up = review.get("follow_up_actions") or []
    risk = derive_risk(signals)

    out = [f"## 계정 {account_id}", ""]

    # 1. 의심 신호 후보
    out.append("### 의심 신호 후보")
    if signals:
        for s in signals:
            name = s.get("signal_name", "")
            out.append(f"- {s.get('signal_id')} {name}".rstrip())
    else:
        out.append("- 특이사항 없음")
    out.append("")

    # 2. 탐지 근거
    out.append("### 탐지 근거")
    if signals:
        for s in signals:
            tids = ", ".join(s.get("related_transaction_ids") or [])
            evidence = (s.get("evidence", "") or "").strip()
            suffix = f" (관련 거래: {tids})" if tids else ""
            out.append(f"- {s.get('signal_id')}: {evidence}{suffix}")
    else:
        # 정상 판단 근거를 summary에서 가져와 명시
        normal = f"- 특이사항 없음. {summary}".rstrip()
        out.append(normal)
    out.append("")

    # 3. 추가 확인 항목
    out.append("### 추가 확인 항목")
    if follow_up:
        for action in follow_up:
            out.append(f"- {action}")
    else:
        out.append("- 없음")
    out.append("")

    # 4. 위험도
    out.append("### 위험도")
    out.append(f"- {_RISK_KR[risk]}")
    out.append("")

    return "\n".join(out)
