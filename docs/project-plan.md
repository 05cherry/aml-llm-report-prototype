# 프로젝트 계획 (Project Plan)

> 이 문서는 GitHub Milestones / Issues / Projects의 **단일 진실 공급원**이다.
> `/sync-plan` 슬래시 커맨드가 이 문서를 읽어 GitHub에 동기화한다.
> 계획이 바뀌면 이 문서를 먼저 고치고 `/sync-plan`을 다시 실행한다.

## 보드 (GitHub Projects)

- 프로젝트명: `aml-llm-report-prototype`
- Status 컬럼: `Todo` / `In progress` / `Done`
- 새로 생성되는 이슈는 모두 `Todo`로 추가한다.

## 마일스톤 & 이슈

각 이슈는 `why`(왜 하는지)와 `DoD`(완료 기준)를 본문에 포함한다.

### M1 — 셋업 & 문제 정의

- **[M1] 레포 구조 + README 초안**
  - why: 문제 정의·범위·비범위를 먼저 고정해 범위 이탈을 방지
  - DoD: README에 목적 / 범위 / 안 하는 것 / 실행법 골격이 작성됨
- **[M1] CLAUDE.md 배치**
  - why: 작업 원칙과 프로젝트 컨텍스트를 에이전트에 고정
  - DoD: 루트에 CLAUDE.md 존재, 4원칙·도메인 규칙·완료 기준 포함
- **[M1] 샘플 거래 데이터 확정**
  - why: 신호 탐지의 입력 기준 확정
  - DoD: data/sample_transactions.json의 5개 시나리오(A~E)가 신호 정의와 일치

### M2 — 핵심 파이프라인

- **[M2] Claude API 연동 + 기본 파이프라인**
  - why: 거래 데이터 입력 → 리포트 출력의 최소 동작 확보
  - DoD: 단일 CLI 명령으로 샘플 데이터를 읽어 계정별 리포트를 출력
- **[M2] 리포트 출력 구조 정의**
  - why: 의심 신호/근거/추가확인/위험도를 일관된 형식으로 제공
  - DoD: 4개 항목 구조가 docs/prompt-design.md에 명시됨
- **[M2] 출력 일관성 확보 (tool 스키마)**
  - why: 프롬프트만으로는 형식이 흔들림. 스키마로 강제
  - DoD: 모든 계정에서 동일한 구조의 출력이 나옴

### M3 — AML 도메인 설계

- **[M3] 의심 신호 기준 정의**
  - why: 탐지 근거의 단일 기준 확보
  - DoD: docs/aml-signals.md에 신호 5개의 정의·근거·기준·필요필드 작성됨
- **[M3] 근거 기록 방식 구현**
  - why: "왜 의심인지 / 어떤 기준에 걸렸는지"가 리포트에 남아야 신뢰 가능
  - DoD: 각 의심 판정에 신호명과 해당 거래·필드 근거가 출력됨
- **[M3] 엣지 케이스 / 오탐 정리**
  - why: 정상 계정 미탐지 및 한계 인식
  - DoD: ACC-E가 "특이사항 없음"으로 출력, 한계가 docs/limitations.md에 정리됨

### M4 — 문서화 & 결과물

- **[M4] sample_report.md 생성**
  - why: 대표 실행 결과를 리뷰어가 즉시 확인
  - DoD: 5개 계정 리포트가 담긴 sample_report.md 존재
- **[M4] screenshots 추가**
  - why: 실행 화면 증빙
  - DoD: PyCharm 실행 + 결과 화면이 screenshots/에 존재
- **[M4] README 완성**
  - why: 실행법·설계 의도·한계·다음 단계 전달
  - DoD: README에 위 항목이 모두 포함됨
- **[M4] 설계 노트 정리**
  - why: 사고 과정(특히 출력 일관성)을 포트폴리오로 남김
  - DoD: docs/prompt-design.md, docs/limitations.md 작성 완료
