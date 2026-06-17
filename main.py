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

DEFAULT_INPUT = "data/sample_transactions.json"
DEFAULT_MODEL = "claude-sonnet-4-6"


def build_report(client, accounts, *, model, system_prompt):
    """5개 계정을 순서대로 검토해 리포트 문자열과 오류 여부를 반환한다."""
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
    for account, txns in accounts:
        aid = account.get("account_id", "?")
        try:
            review = review_account(client, account, txns, model=model, system_prompt=system_prompt)
            blocks.append(render(review))
        except Exception as exc:  # 한 계정 실패가 전체를 막지 않도록 계속 진행
            had_error = True
            print(f"경고: 계정 {aid} 검토 실패: {exc}", file=sys.stderr)
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

    report, had_error = build_report(client, accounts, model=args.model, system_prompt=system_prompt)

    print(report)
    if args.out:
        Path(args.out).write_text(report, encoding="utf-8")
        print(f"\n리포트를 {args.out} 에 저장했습니다.", file=sys.stderr)

    return 1 if had_error else 0


if __name__ == "__main__":
    sys.exit(main())
