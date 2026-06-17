"""Claude 호출 및 구조화 출력(tool use) 처리.

계정 1개당 API 호출 1회. tool_choice로 submit_aml_review 호출을 강제해
출력 형식을 스키마로 고정한다(docs/prompt-design.md).
"""

import json
from pathlib import Path

# 신호 정의 문서는 모듈 기준 상대 경로 + UTF-8로 읽는다.
# (Windows 기본 코드페이지(cp949)로 읽으면 한글이 깨지므로 encoding 명시 필수)
_DOCS_DIR = Path(__file__).resolve().parent.parent / "docs"
_SIGNALS_DOC = _DOCS_DIR / "aml-signals.md"

# docs/prompt-design.md에 정의된 스키마를 그대로 사용한다.
TOOL = {
    "name": "submit_aml_review",
    "description": "한 계정에 대한 AML 1차 검토 결과를 구조화하여 제출한다.",
    "input_schema": {
        "type": "object",
        "properties": {
            "account_id": {"type": "string"},
            "risk_level": {
                "type": "string",
                "enum": ["none", "medium", "high"],
                "description": "docs/aml-signals.md의 위험도 규칙을 따른다.",
            },
            "summary": {
                "type": "string",
                "description": "검토 결과 한 줄 요약. risk_level이 none이면 정상 판단 근거를 간단히 포함.",
            },
            "signals": {
                "type": "array",
                "description": "탐지된 의심 신호 목록. 없으면 빈 배열.",
                "items": {
                    "type": "object",
                    "properties": {
                        "signal_id": {"type": "string", "enum": ["S1", "S2", "S3", "S4", "S5"]},
                        "signal_name": {"type": "string"},
                        "evidence": {
                            "type": "string",
                            "description": "어떤 거래/필드가 어떤 기준에 걸렸는지 구체적으로.",
                        },
                        "related_transaction_ids": {
                            "type": "array",
                            "items": {"type": "string"},
                        },
                    },
                    "required": ["signal_id", "signal_name", "evidence", "related_transaction_ids"],
                },
            },
            "follow_up_actions": {
                "type": "array",
                "description": "담당자가 추가로 확인할 항목. 정상이면 빈 배열 가능.",
                "items": {"type": "string"},
            },
        },
        "required": ["account_id", "risk_level", "summary", "signals", "follow_up_actions"],
    },
}


def load_signal_rules():
    """docs/aml-signals.md 본문을 그대로 반환한다(검증/주입용)."""
    return _SIGNALS_DOC.read_text(encoding="utf-8")


def build_system_prompt(signal_rules=None):
    """시스템 프롬프트를 구성한다.

    역할 + 신호 정의 문서(verbatim 주입) + 일반 판정 규칙으로만 구성한다.
    불변식: 이 문자열에는 특정 계정 ID(ACC-)나 거래 ID(T-)가 들어가지 않는다.
    """
    rules = signal_rules if signal_rules is not None else load_signal_rules()
    return (
        "당신은 가상자산 거래소의 자금세탁방지(AML) 1차 검토를 보조하는 도우미다.\n"
        "아래 '신호 정의 문서'에 정의된 기준에만 근거해 의심 거래 후보와 사유를 제시한다.\n"
        "근거를 댈 수 없으면 신호로 분류하지 않는다. 문서에 없는 기준을 임의로 만들지 않는다.\n"
        "모든 신호에는 related_transaction_ids로 실제 거래 근거를 연결한다.\n"
        "\n"
        "추가 판정 규칙:\n"
        "- (A1) 신고 소득 구간(kyc_income_band)에 상한이 정의되지 않은 구간은\n"
        "  S5의 '소득 상한의 3배' 검사를 평가할 수 없다. 그 근거만으로 S5를 판정하지 않는다.\n"
        "- (A2) S2(통과 계좌)는 입금→출금 구간 내에 trade 거래가 0건일 때만 성립한다.\n"
        "\n"
        "충족 신호가 없으면 risk_level을 none, signals를 빈 배열로 두고\n"
        "summary에 정상으로 판단한 근거를 간단히 적는다(모든 계정을 의심으로 찍지 않는다).\n"
        "반드시 submit_aml_review 도구로만 결과를 제출한다.\n"
        "\n"
        "=== 신호 정의 문서 (docs/aml-signals.md) ===\n"
        f"{rules}\n"
    )


def build_user_message(account, transactions):
    """분석 대상 계정 1건의 프로필 + 거래 목록(JSON)을 user 메시지로 만든다."""
    payload = {"account": account, "transactions": transactions}
    return (
        "다음 계정 1건을 신호 정의 기준으로 검토하고 submit_aml_review 도구로 결과를 제출하라.\n\n"
        + json.dumps(payload, ensure_ascii=False, indent=2)
    )


def review_account(client, account, transactions, *, model, system_prompt):
    """계정 1건을 Claude로 검토하고, tool 입력(dict)을 반환한다."""
    resp = client.messages.create(
        model=model,
        max_tokens=1024,
        temperature=0,
        system=system_prompt,
        tools=[TOOL],
        tool_choice={"type": "tool", "name": "submit_aml_review"},
        messages=[{"role": "user", "content": build_user_message(account, transactions)}],
    )
    for block in resp.content:
        if block.type == "tool_use" and block.name == "submit_aml_review":
            return dict(block.input)
    raise RuntimeError(f"{account.get('account_id')}: submit_aml_review 도구 호출 결과를 찾을 수 없습니다.")
