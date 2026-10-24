"""
data_store.py
Modular data layer for Dukaan Dost.
All amounts stored in integer paise (1 rupee = 100 paise) to avoid floating-point errors.
Replace the JSON file backend with a real DB by implementing the same interface.
"""

import json
import uuid
import os
from datetime import datetime, date
from typing import Optional, List, Dict, Any

DATA_FILE = "dukaan_dost_data.json"

VALID_TYPES = {"sale", "expense", "credit_given"}


# ─── Data Model ────────────────────────────────────────────────────────────────

def make_transaction(
    type: str,
    amount_paise: int,
    customer_name: Optional[str] = None,
    category: Optional[str] = None,
    description: Optional[str] = None,
    original_transcript: Optional[str] = None,
    language: str = "hi-IN",
    confirmation_status: str = "confirmed",
) -> Dict[str, Any]:
    """Create a new transaction dict. amount_paise must be a positive integer."""
    if type not in VALID_TYPES:
        raise ValueError(f"Invalid type '{type}'. Must be one of {VALID_TYPES}")
    if not isinstance(amount_paise, int) or amount_paise <= 0:
        raise ValueError("amount_paise must be a positive integer")
    return {
        "id": str(uuid.uuid4()),
        "type": type,
        "amount_paise": amount_paise,
        "customer_name": customer_name,
        "category": category,
        "description": description,
        "original_transcript": original_transcript,
        "language": language,
        "created_at": datetime.now().isoformat(),
        "confirmation_status": confirmation_status,
    }


# ─── Persistence ───────────────────────────────────────────────────────────────

def _load_all() -> List[Dict[str, Any]]:
    if not os.path.exists(DATA_FILE):
        return []
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, list) else []
    except (json.JSONDecodeError, OSError):
        return []


def _save_all(transactions: List[Dict[str, Any]]) -> None:
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(transactions, f, ensure_ascii=False, indent=2)


def save_transaction(tx: Dict[str, Any]) -> Dict[str, Any]:
    """Persist a transaction and return it."""
    all_tx = _load_all()
    all_tx.append(tx)
    _save_all(all_tx)
    return tx


def get_all_transactions() -> List[Dict[str, Any]]:
    return _load_all()


def delete_transaction(tx_id: str) -> bool:
    all_tx = _load_all()
    new_list = [t for t in all_tx if t["id"] != tx_id]
    if len(new_list) == len(all_tx):
        return False
    _save_all(new_list)
    return True


# ─── Queries ───────────────────────────────────────────────────────────────────

def get_transactions_today() -> List[Dict[str, Any]]:
    today = date.today().isoformat()
    return [
        t for t in _load_all()
        if t.get("created_at", "").startswith(today)
    ]


def get_transactions_by_type(tx_type: str) -> List[Dict[str, Any]]:
    return [t for t in _load_all() if t.get("type") == tx_type]


def get_transactions_by_customer(customer_name: str) -> List[Dict[str, Any]]:
    name_lower = customer_name.lower()
    return [
        t for t in _load_all()
        if (t.get("customer_name") or "").lower() == name_lower
    ]


def get_customer_outstanding(customer_name: str) -> int:
    """Return total outstanding paise for a customer (credit_given transactions only)."""
    txs = get_transactions_by_customer(customer_name)
    return sum(
        t["amount_paise"] for t in txs
        if t.get("type") == "credit_given"
    )


def get_all_customers_outstanding() -> Dict[str, int]:
    """Return {customer_name: total_outstanding_paise} for all customers with credit."""
    result: Dict[str, int] = {}
    for t in _load_all():
        if t.get("type") == "credit_given" and t.get("customer_name"):
            name = t["customer_name"]
            result[name] = result.get(name, 0) + t["amount_paise"]
    return result


# ─── Dashboard Totals ──────────────────────────────────────────────────────────

def get_dashboard_totals() -> Dict[str, int]:
    """Derive today's totals from stored transactions. Returns paise."""
    today_txs = get_transactions_today()
    sales = sum(t["amount_paise"] for t in today_txs if t.get("type") == "sale")
    expenses = sum(t["amount_paise"] for t in today_txs if t.get("type") == "expense")
    credits = sum(t["amount_paise"] for t in today_txs if t.get("type") == "credit_given")
    outstanding = sum(get_all_customers_outstanding().values())
    return {
        "sales_today_paise": sales,
        "expenses_today_paise": expenses,
        "credit_given_today_paise": credits,
        "total_outstanding_paise": outstanding,
    }


# ─── Helpers ──────────────────────────────────────────────────────────────────

def paise_to_rupees(paise: int) -> str:
    """Format paise as readable rupee string, e.g. 150050 → '₹1,500.50'."""
    rupees = paise / 100
    if rupees == int(rupees):
        return f"₹{int(rupees):,}"
    return f"₹{rupees:,.2f}"


def rupees_to_paise(rupees: float) -> int:
    """Convert rupee float to exact integer paise."""
    return round(rupees * 100)


# ─── Sample Data ──────────────────────────────────────────────────────────────

SAMPLE_TRANSACTIONS = [
    make_transaction("sale", 150000, description="सुबह की बिक्री", language="hi-IN",
                     original_transcript="आज 1500 रुपये की बिक्री हुई।"),
    make_transaction("credit_given", 50000, customer_name="Ramesh",
                     description="उधार दिया", language="hi-IN",
                     original_transcript="Ramesh ne 500 rupaye udhaar liye."),
    make_transaction("expense", 30000, category="Supplies",
                     description="दुकान का सामान", language="hi-IN",
                     original_transcript="आज दुकान के लिए 300 रुपये का सामान खरीदा।"),
    make_transaction("sale", 75000, description="शाम की बिक्री", language="hi-IN",
                     original_transcript="आज 750 रुपये की बिक्री हुई।"),
    make_transaction("credit_given", 20000, customer_name="Sunita",
                     description="बाकी उधार", language="hi-IN",
                     original_transcript="Sunita ne 200 rupaye udhaar liye."),
]


def seed_sample_data() -> None:
    """Insert sample transactions if the data file is empty."""
    if not _load_all():
        for tx in SAMPLE_TRANSACTIONS:
            save_transaction(tx)
