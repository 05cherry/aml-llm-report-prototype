"""입력 거래 데이터 로딩 및 계정 단위 그룹화."""

import json
from pathlib import Path


def load_data(path):
    """JSON 입력 파일을 읽어 dict로 반환한다. (UTF-8)"""
    p = Path(path)
    data = json.loads(p.read_text(encoding="utf-8"))
    if "accounts" not in data or "transactions" not in data:
        raise ValueError(f"입력 파일에 accounts/transactions 키가 없습니다: {path}")
    return data


def group_by_account(data):
    """계정별로 (account, [transactions]) 목록을 만든다.

    accounts 배열의 순서를 그대로 유지해 출력 순서를 결정적으로 만든다(A→E).
    """
    txns_by_acc = {}
    for t in data["transactions"]:
        txns_by_acc.setdefault(t["account_id"], []).append(t)

    grouped = []
    for account in data["accounts"]:
        aid = account["account_id"]
        grouped.append((account, txns_by_acc.get(aid, [])))
    return grouped
