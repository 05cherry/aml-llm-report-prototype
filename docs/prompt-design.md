# 프롬프트 & 출력 설계 (Prompt & Output Design)

## 목적

LLM이 계정별 AML 검토 결과를 **매번 동일한 구조로, 근거와 함께** 출력하도록
설계 방식을 정의한다. 신호 정의 자체는 `docs/aml-signals.md`를 기준으로 한다.

## 왜 프롬프트가 아니라 tool 스키마인가

프롬프트로 "JSON으로 답해줘"라고 지시하는 방식은 형식이 자주 흔들린다
(필드 누락, 임의 키 추가, 설명 문장 혼입 등). 본 프로토타입은 Claude의
**tool use(구조화 출력)** 를 사용해 출력 형식을 스키마로 강제한다.

- 검토 결과 제출용 tool을 하나 정의하고, `tool_choice`로 그 tool을 **강제 호출**한다.
- 모델은 자유 텍스트가 아니라 스키마에 맞는 입력을 생성하므로, 필수 필드를
  비울 수 없다. 즉 "근거 없는 의심 판정"이 구조적으로 불가능해진다.
- 코드는 tool 호출의 입력(JSON)을 그대로 읽어 리포트(Markdown)로 렌더링한다.
  (tool은 실제로 무언가를 실행하지 않는다. 출력 형식 고정용 장치다.)

## 호출 단위: 계정당 1회

여러 계정을 한 번에 분석하면 모델이 계정 간 근거를 섞을 위험이 있다.
**계정 1개 = API 호출 1회**로 분리해 근거 귀속을 명확히 하고 일관성을 높인다.

## tool 스키마

```json
{
  "name": "submit_aml_review",
  "description": "한 계정에 대한 AML 1차 검토 결과를 구조화하여 제출한다.",
  "input_schema": {
    "type": "object",
    "properties": {
      "account_id": { "type": "string" },
      "risk_level": {
        "type": "string",
        "enum": ["none", "medium", "high"],
        "description": "docs/aml-signals.md의 위험도 규칙을 따른다."
      },
      "summary": {
        "type": "string",
        "description": "검토 결과 한 줄 요약. risk_level이 none이면 정상 판단 근거를 간단히 포함."
      },
      "signals": {
        "type": "array",
        "description": "탐지된 의심 신호 목록. 없으면 빈 배열.",
        "items": {
          "type": "object",
          "properties": {
            "signal_id": { "type": "string", "enum": ["S1", "S2", "S3", "S4", "S5"] },
            "signal_name": { "type": "string" },
            "evidence": {
              "type": "string",
              "description": "어떤 거래/필드가 어떤 기준에 걸렸는지 구체적으로."
            },
            "related_transaction_ids": {
              "type": "array",
              "items": { "type": "string" }
            }
          },
          "required": ["signal_id", "signal_name", "evidence", "related_transaction_ids"]
        }
      },
      "follow_up_actions": {
        "type": "array",
        "description": "담당자가 추가로 확인할 항목. 정상이면 빈 배열 가능.",
        "items": { "type": "string" }
      }
    },
    "required": ["account_id", "risk_level", "summary", "signals", "follow_up_actions"]
  }
}
```

## 리포트 4항목 매핑

| 리포트 항목 | 스키마 필드 |
|-------------|-------------|
| 위험도 | `risk_level` |
| 의심 신호 후보 | `signals[].signal_id`, `signals[].signal_name` |
| 탐지 근거 | `signals[].evidence`, `signals[].related_transaction_ids` |
| 추가 확인 항목 | `follow_up_actions[]` |

## 프롬프트 구성

- **system**: 역할(AML 1차 검토 보조) + `docs/aml-signals.md`의 신호 정의·임계값·
  위험도 규칙을 주입. "정의된 신호 기준에만 근거하고, 근거 없는 추측은 하지 말 것"을 명시.
- **user**: 분석 대상 계정 1건의 KYC 프로필 + 해당 계정의 거래 목록(JSON).
- **tool_choice**: `submit_aml_review`를 강제 호출.

## 일관성 · 근거 규칙

- 온도(temperature)는 낮게 설정해 출력 변동을 줄인다.
- 모든 신호에는 `related_transaction_ids`로 실제 거래 근거를 연결한다.
  근거를 댈 수 없으면 신호로 분류하지 않는다.
- 신호가 없으면 `risk_level: "none"`, `signals: []`, `summary`에 정상 판단 근거를
  간단히 기재한다 (모든 계정을 의심으로 찍지 않는 것이 핵심).
- 위험도는 코드에서 신호 결과로 한 번 더 검증할 수 있다
  (예: S4 포함 또는 신호 2개 이상이면 high). 문서 규칙과 출력이 어긋나면 문서 우선.
