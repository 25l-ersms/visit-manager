import os
from typing import List, NamedTuple


class Transaction(NamedTuple):
    id: str
    amount: int
    currency: str


FILE_PATH = "/app/visit_manager/data/charges.txt"


def list_transactions(path: str = FILE_PATH) -> List[Transaction]:
    """
    Wczytuje wszystkie transakcje z pliku i zwraca je jako listę Transaction.
    """
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as file:
        lines = [line.strip() for line in file if line.strip()]
    txs: List[Transaction] = []
    for line in lines:
        tx_id, amt, cur = line.split(",", 2)
        txs.append(Transaction(id=tx_id, amount=int(amt), currency=cur))
    return txs


def add_transaction(tx_id: str, amount: int, currency: str, path: str = FILE_PATH) -> None:
    """
    Dopisuje nową transakcję na koniec pliku.
    """
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(f"{tx_id},{amount},{currency}\n")


def delete_transaction(tx_id: str, path: str = FILE_PATH) -> None:
    """
    Usuwa z pliku transakcję o zadanym ID.
    Zwraca KeyError, jeśli nie znaleziono.
    """
    txs = list_transactions(path)
    filtered = [t for t in txs if t.id != tx_id]
    if len(filtered) == len(txs):
        raise KeyError(f"Transaction {tx_id} not found")
    with open(path, "w", encoding="utf-8") as f:
        for t in filtered:
            f.write(f"{t.id},{t.amount},{t.currency}\n")


def delete_last_transaction(path: str = FILE_PATH) -> Transaction:
    """
    Usuwa ostatnią transakcję w pliku.
    Zwraca IndexError, jeśli plik jest pusty.
    """
    txs = list_transactions(path)
    if not txs:
        raise IndexError("No transactions to delete")
    last = txs[-1]
    delete_transaction(last.id, path)
    return last
