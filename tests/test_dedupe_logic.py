"""
Test Deduplication Logic
Tests for composite key deduplication (vendor + invoice_number + date + amount).
"""

import pytest
from typing import List, Dict, Any


def generate_composite_key(invoice: Dict[str, Any]) -> str:
    """Generate deduplication key from invoice fields."""
    vendor = (invoice.get("vendor") or "").strip().lower()
    invoice_number = (invoice.get("invoice_number") or "").strip().lower()
    invoice_date = (invoice.get("invoice_date") or "").strip()
    amount = str(invoice.get("amount") or "").strip()
    
    return f"{vendor}|{invoice_number}|{invoice_date}|{amount}"


def check_duplicate(existing_invoices: List[Dict], new_invoice: Dict) -> bool:
    """Check if new_invoice is duplicate of any existing."""
    new_key = generate_composite_key(new_invoice)
    
    for existing in existing_invoices:
        if generate_composite_key(existing) == new_key:
            return True
    return False


def find_duplicate_row(existing_invoices: List[Dict], new_invoice: Dict) -> int:
    """Return index of duplicate row, or -1 if not found."""
    new_key = generate_composite_key(new_invoice)
    
    for idx, existing in enumerate(existing_invoices):
        if generate_composite_key(existing) == new_key:
            return idx
    return -1


class TestDeduplication:
    
    def test_exact_duplicate_detected(self):
        existing = [{
            "vendor": "PT Sumber Makmur",
            "invoice_number": "INV-2026-00123",
            "invoice_date": "2026-08-10",
            "amount": 15000000
        }]
        new = {
            "vendor": "PT Sumber Makmur",
            "invoice_number": "INV-2026-00123",
            "invoice_date": "2026-08-10",
            "amount": 15000000
        }
        assert check_duplicate(existing, new) == True
    
    def test_case_insensitive_vendor(self):
        existing = [{"vendor": "PT Sumber Makmur", "invoice_number": "INV-001", "invoice_date": "2026-08-10", "amount": 1000000}]
        new = {"vendor": "pt sumber makmur", "invoice_number": "INV-001", "invoice_date": "2026-08-10", "amount": 1000000}
        assert check_duplicate(existing, new) == True
    
    def test_whitespace_handling(self):
        existing = [{"vendor": "  PT Test  ", "invoice_number": "  INV-001  ", "invoice_date": "2026-08-10", "amount": 1000000}]
        new = {"vendor": "PT Test", "invoice_number": "INV-001", "invoice_date": "2026-08-10", "amount": 1000000}
        assert check_duplicate(existing, new) == True
    
    def test_different_amount_not_duplicate(self):
        existing = [{"vendor": "PT Test", "invoice_number": "INV-001", "invoice_date": "2026-08-10", "amount": 1000000}]
        new = {"vendor": "PT Test", "invoice_number": "INV-001", "invoice_date": "2026-08-10", "amount": 2000000}
        assert check_duplicate(existing, new) == False
    
    def test_different_invoice_number_not_duplicate(self):
        existing = [{"vendor": "PT Test", "invoice_number": "INV-001", "invoice_date": "2026-08-10", "amount": 1000000}]
        new = {"vendor": "PT Test", "invoice_number": "INV-002", "invoice_date": "2026-08-10", "amount": 1000000}
        assert check_duplicate(existing, new) == False
    
    def test_different_date_not_duplicate(self):
        existing = [{"vendor": "PT Test", "invoice_number": "INV-001", "invoice_date": "2026-08-10", "amount": 1000000}]
        new = {"vendor": "PT Test", "invoice_number": "INV-001", "invoice_date": "2026-08-11", "amount": 1000000}
        assert check_duplicate(existing, new) == False
    
    def test_different_vendor_not_duplicate(self):
        existing = [{"vendor": "PT Test A", "invoice_number": "INV-001", "invoice_date": "2026-08-10", "amount": 1000000}]
        new = {"vendor": "PT Test B", "invoice_number": "INV-001", "invoice_date": "2026-08-10", "amount": 1000000}
        assert check_duplicate(existing, new) == False
    
    def test_find_duplicate_row_index(self):
        existing = [
            {"vendor": "PT A", "invoice_number": "INV-001", "invoice_date": "2026-08-10", "amount": 1000000},
            {"vendor": "PT B", "invoice_number": "INV-002", "invoice_date": "2026-08-11", "amount": 2000000},
        ]
        new = {"vendor": "PT B", "invoice_number": "INV-002", "invoice_date": "2026-08-11", "amount": 2000000}
        assert find_duplicate_row(existing, new) == 1
    
    def test_no_duplicate_returns_false(self):
        existing = [{"vendor": "PT A", "invoice_number": "INV-001", "invoice_date": "2026-08-10", "amount": 1000000}]
        new = {"vendor": "PT B", "invoice_number": "INV-002", "invoice_date": "2026-08-11", "amount": 2000000}
        assert check_duplicate(existing, new) == False
        assert find_duplicate_row(existing, new) == -1
    
    def test_empty_fields_handling(self):
        existing = [{"vendor": "", "invoice_number": "INV-001", "invoice_date": "2026-08-10", "amount": 1000000}]
        new = {"vendor": None, "invoice_number": "INV-001", "invoice_date": "2026-08-10", "amount": 1000000}
        assert check_duplicate(existing, new) == True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])