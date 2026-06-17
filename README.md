# AML LLM 리포트 프로토타입

준법감시(AML) 1차 검토를 보조하는 **LLM 기반 리포트 생성** 프로토타입.
더미 거래 데이터(JSON)를 입력받아, 계정별 자금세탁 의심 신호와 근거를 담은
검토 리포트(Markdown)를 생성한다.

> ⚠️ **면접용 데모**입니다. 모든 입력은 더미 데이터이며, 임계값은 시연용
> 예시값(실제 규제 기준 아님)입니다. 신호 탐지는 의심거래 확정이 아니라
> "담당자가 추가 확인할 후보"를 의미합니다.

---

## 목적과 범위

- **목적**: 거래 데이터에서 AML 의심 신호 후보를 1차로 골라내고, **왜 의심인지에
  대한 근거**(어떤 신호 / 어떤 거래·필드)를 일관된 형식으로 제시한다.
- **범위 (하는 것)**: 단일 CLI로 5개 계정 더미 데이터를 읽어 계정별 리포트 생성.
  신호 판정은 LLM이, 형식·위험도는 코드가 고정한다.
- **안 하는 것 (범위 밖)**: 웹 UI·DB·인증·비동기 큐, 실제 규제 임계값, 외부 위험주소
  DB 연계, 실데이터 처리. CLI로 충분하다.

## 빠른 시작

```bash
# 1. 가상환경 + 의존성 (Python 3.13)
python -m venv .venv
.venv\Scripts\activate          # Windows (macOS/Linux: source .venv/bin/activate)
pip install -r requirements.txt # anthropic, python-dotenv

# 2. API 키 설정
copy .env.example .env          # (macOS/Linux: cp .env.example .env)
# .env 파일에 ANTHROPIC_API_KEY=sk-ant-... 입력

# 3. 실행 — 5개 계정 리포트 생성
python main.py                          # 표준출력으로 리포트
python main.py --out sample_report.md   # 파일로도 저장
```

실행 중 진행 상황은 stderr로 출력된다(리포트 본문은 stdout):

```
입력 로드 완료: data/sample_transactions.json (계정 5개)
모델 claude-sonnet-4-6 로 계정별 AML 검토를 시작합니다.

[1/5] ACC-A 검토 중... (거래 6건)
        ✓ ACC-A: 신호 [S1] → 위험도 중간
[2/5] ACC-B 검토 중... (거래 2건)
        ✓ ACC-B: 신호 [S2] → 위험도 중간
...
모든 계정 검토 완료.
```

대표 실행 결과는 [`sample_report.md`](sample_report.md) 참고.

### 오프라인 테스트 (실 API/키 불필요)

```bash
python test_offline.py
```

위험도 파생 로직, 5계정 출력 구조 동일성, 시스템 프롬프트 무-ID 불변식,
문서 UTF-8 로드를 실 API 호출 없이 검증한다.

## 설계 의도

이 프로토타입의 핵심은 "LLM이 자유롭게 답하게 두지 않는 것"이다.

1. **신호 정의는 문서가 단일 진실 공급원(SSoT)**
   S1~S5 신호의 정의·임계값·위험도 규칙은 [`docs/aml-signals.md`](docs/aml-signals.md)에만
   존재한다. 코드는 이 문서를 런타임에 읽어 시스템 프롬프트에 주입할 뿐, 임계값을
   코드에 하드코딩하지 않는다. 규칙을 바꾸려면 문서를 먼저 고친다.

2. **출력 형식은 프롬프트가 아니라 tool 스키마로 강제**
   "JSON으로 답해줘" 식 지시는 형식이 흔들린다. 대신 `submit_aml_review` tool을
   정의하고 `tool_choice`로 강제 호출한다. `evidence`·`related_transaction_ids`를
   필수 필드로 두어 **근거 없는 의심 판정이 구조적으로 불가능**하게 만든다.
   ([`docs/prompt-design.md`](docs/prompt-design.md))

3. **계정당 1회 호출**
   여러 계정을 한 번에 분석하면 근거가 섞일 수 있어, 계정 1개 = API 호출 1회로
   분리해 근거 귀속을 명확히 한다.

4. **위험도는 코드가 파생(모델 값 무시)**
   모델이 신호는 맞게 잡고 위험도만 틀리는 경우를 막기 위해, 위험도는 모델 출력이
   아니라 `src/signals.py`의 `derive_risk(signals)`가 문서 위험도 표를 적용해 파생한
   값을 권위로 렌더링한다.

5. **과탐지 방지 가드(일반 규칙)**
   시스템 프롬프트에 정답 맞추기식 튜닝(특정 계정/거래 ID) 없이 일반 규칙만 둔다:
   (A1) 상한 미정의 소득구간은 S5 정량 평가 불가, (A2) S2는 구간 내 trade 0건 필요.

## 프로젝트 구조

```
main.py                       # CLI 진입점
src/
  loader.py                   # JSON 로드 + 계정별 그룹화(A→E 순서)
  reviewer.py                 # 프롬프트 구성 + tool 강제 호출 + 파싱
  signals.py                  # derive_risk: 문서 위험도 표 기반 파생
  renderer.py                 # 검토 결과 → 4개 섹션 Markdown
test_offline.py               # 오프라인 테스트
data/sample_transactions.json # 더미 입력 (5개 시나리오 A~E)
docs/
  aml-signals.md              # AML 신호 정의 (도메인 규칙 SSoT)
  prompt-design.md            # 프롬프트·출력·스키마 설계 노트
  limitations.md              # 한계 및 엣지 케이스
sample_report.md              # 대표 실행 결과물
```

## AML 신호 요약

| ID | 신호 | 한 줄 정의 |
|----|------|-----------|
| S1 | 구조화 거래 | 보고 임계금액 바로 아래 금액으로 분할 입출금 반복 |
| S2 | 통과 계좌 | 입금 직후 거의 전액 출금, 그 사이 매매 없음 |
| S3 | 신규 계정 대량 거래 | 개설 직후 계정의 과도한 거래량 |
| S4 | 고위험 주소 연관 | 믹서/다크넷/제재/기등록 위험 지갑과의 입출금 |
| S5 | KYC 프로필 불일치 | 신고 소득·직업 대비 과도한 거래 규모 |

위험도: **High**(S4 포함 또는 신호 2개↑) / **Medium**(단일 신호) /
**None**(미충족 → "특이사항 없음"). 자세한 기준은 [`docs/aml-signals.md`](docs/aml-signals.md).

## 한계

시연용 임계값, LLM 비결정성과 오탐 전제, 프롬프트 가드의 한계, 계정 간 패턴
미탐지 등은 [`docs/limitations.md`](docs/limitations.md)에 정리했다.

## 다음 단계 (프로토타입 범위 밖)

- 실제 규제 기준값 반영 및 임계값 튜닝
- 시계열·네트워크 기반 패턴 탐지(분산 이동, 순환 거래 등) 추가
- 외부 위험 주소 DB(체이널리시스 등) 연계
- 운영 데이터 적용 시 개인정보 국외이전·망분리 검토
