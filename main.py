"""AML 1차 검토 리포트 생성 CLI.

단일 명령으로 더미 거래 데이터(JSON)를 읽어 계정별 AML 검토 리포트(Markdown)를
생성한다.

    python main.py                                  # 기본 입력/표준출력
    python main.py data/sample_transactions.json    # 입력 경로 지정
    python main.py --out sample_report.md           # 파일로도 저장
"""

import argparse
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
import anthropic

from src.loader import load_data, group_by_account
from src.reviewer import review_account, build_system_prompt
from src.renderer import render
from src.signals import derive_risk

DEFAULT_INPUT = "data/sample_transactions.json"
DEFAULT_MODEL = "claude-sonnet-4-6"


_RISK_LABEL = {"none": "낮음", "medium": "중간", "high": "높음"}


def build_report(client, accounts, *, model, system_prompt):
    """5개 계정을 순서대로 검토해 리포트 문자열과 오류 여부를 반환한다.

    진행 상황은 stderr로 출력한다(리포트 본문은 stdout, 로그는 stderr로 분리).
    """
    blocks = [
        "# AML 1차 검토 리포트",
        "",
        f"- 모델: {model}",
        f"- 계정 수: {len(accounts)}",
        "",
        "---",
        "",
    ]
    had_error = False
    total = len(accounts)
    for idx, (account, txns) in enumerate(accounts, start=1):
        aid = account.get("account_id", "?")
        print(f"[{idx}/{total}] {aid} 검토 중... (거래 {len(txns)}건)", file=sys.stderr)
        try:
            review = review_account(client, account, txns, model=model, system_prompt=system_prompt)
            signals = review.get("signals") or []
            ids = [s.get("signal_id") for s in signals]
            risk = derive_risk(signals)
            detail = ", ".join(ids) if ids else "특이사항 없음"
            print(
                f"        ✓ {aid}: 신호 [{detail}] → 위험도 {_RISK_LABEL.get(risk, risk)}",
                file=sys.stderr,
            )
            blocks.append(render(review))
        except Exception as exc:  # 한 계정 실패가 전체를 막지 않도록 계속 진행
            had_error = True
            print(f"        ✗ {aid} 검토 실패: {exc}", file=sys.stderr)
            blocks.append(f"## 계정 {aid}\n\n검토 실패: {exc}\n")
    return "\n".join(blocks), had_error


def main(argv=None):
    parser = argparse.ArgumentParser(description="AML 1차 검토 리포트 생성")
    parser.add_argument("input", nargs="?", default=DEFAULT_INPUT, help="입력 거래 JSON 경로")
    parser.add_argument("--out", help="리포트를 저장할 파일 경로 (지정 시 표준출력에도 출력)")
    parser.add_argument("--model", default=DEFAULT_MODEL, help="사용할 Claude 모델 ID")
    args = parser.parse_args(argv)

    load_dotenv()
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print(
            "오류: ANTHROPIC_API_KEY가 설정되지 않았습니다. "
            ".env.example을 참고해 .env에 키를 설정하세요.",
            file=sys.stderr,
        )
        return 1

    client = anthropic.Anthropic(api_key=api_key)
    data = load_data(args.input)
    accounts = group_by_account(data)
    system_prompt = build_system_prompt()
    print(f"입력 로드 완료: {args.input} (계정 {len(accounts)}개)", file=sys.stderr)
    print(f"모델 {args.model} 로 계정별 AML 검토를 시작합니다.\n", file=sys.stderr)

    report, had_error = build_report(client, accounts, model=args.model, system_prompt=system_prompt)

    print(report)
    if args.out:
        Path(args.out).write_text(report, encoding="utf-8")
        print(f"\n리포트를 {args.out} 에 저장했습니다.", file=sys.stderr)

    status = "일부 계정 검토 실패" if had_error else "모든 계정 검토 완료"
    print(f"\n{status}.", file=sys.stderr)
    return 1 if had_error else 0


if __name__ == "__main__":
    sys.exit(main())
