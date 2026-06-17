---
description: docs/project-plan.md를 읽어 GitHub Milestones/Issues/Projects에 동기화 (중복 생성 없음)
allowed-tools: Bash(gh:*), Read
---

`docs/project-plan.md`의 계획을 GitHub에 동기화한다.
**핵심 원칙: 생성만 하고, 이미 존재하는 항목은 다시 만들지 않는다 (idempotent).**

## 절차

1. **계획 읽기**: `docs/project-plan.md`를 읽어 보드 컬럼, 마일스톤, 이슈 목록(제목·why·DoD)을 파악한다.

2. **레포 확인**: `gh repo view --json nameWithOwner -q .nameWithOwner` 로 현재 레포를 확인한다.
   (`gh api`의 `{owner}`/`{repo}` 플레이스홀더는 현재 디렉토리 레포로 자동 치환된다.)

3. **마일스톤 동기화**
   - 기존 목록 조회: `gh api repos/{owner}/{repo}/milestones --jq '.[].title'`
   - 계획에 있으나 GitHub에 없는 마일스톤만 생성:
     `gh api repos/{owner}/{repo}/milestones -f title="M1 — 셋업 & 문제 정의"`
   - 이미 있으면 건너뛴다.

4. **이슈 동기화**
   - 기존 이슈 제목 조회: `gh issue list --state all --limit 100 --json title --jq '.[].title'`
   - 계획에 있으나 없는 이슈만 생성. body에는 계획의 `why`와 `DoD`를 포함하고,
     `[M1]` 등 접두사로 해당 마일스톤에 연결한다:
     `gh issue create --title "[M1] 레포 구조 + README 초안" --body "..." --milestone "M1 — 셋업 & 문제 정의"`
   - 제목이 이미 존재하면 건너뛴다.

5. **Projects 보드 동기화**
   - 보드 존재 확인: `gh project list --owner @me --format json`
   - 없으면 생성: `gh project create --owner @me --title "aml-llm-report-prototype"`
   - Status 필드에 `Todo`/`In progress`/`Done` 옵션이 있는지 확인한다.
   - 이번에 새로 만든 이슈를 보드에 추가하고 Status를 `Todo`로 설정한다:
     `gh project item-add <number> --owner @me --url <issue-url>`
     (Status 설정은 `gh project field-list` / `gh project item-edit`, 필요 시 `gh api graphql` 사용)
   - **권한 주의**: Projects는 `project` 스코프가 필요하다. 권한 오류가 나면
     임의로 우회하지 말고, 사용자에게 다음을 안내한 뒤 보드 단계만 건너뛴다:
     `gh auth refresh -s project,read:project`

6. **요약 출력**: 생성한 마일스톤 수 / 이슈 수 / 건너뛴 수 / 보드 상태를 표로 보고한다.

## 금지 사항

- 기존 이슈·마일스톤을 **삭제하거나 수정하지 않는다** (생성 전용).
- 같은 제목을 중복 생성하지 않는다. 반드시 존재 여부를 먼저 확인한다.
- 인증·권한 오류를 임의로 우회하지 않는다. 사용자에게 알리고 멈춘다.
