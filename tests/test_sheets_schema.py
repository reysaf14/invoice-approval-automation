"""
Test Google Sheets Schema Validation
Tests for invoice row structure and required fields.
"""

import pytest
from typing import Dict, Any, List
from datetime import datetime


REQUIRED_FIELDS = [
    "invoice_id",
    "received_at",
    "vendor",
    "invoice_date",
    "invoice_number",
    "amount",
    "status",
    "confidence",
    "drive_file_id",
    "drive_file_link",
    "source",
    "created_at",
    "updated_at"
]

OPTIONAL_FIELDS = [
    "approved_at",
    "approved_by",
    "rejected_at",
    "reject_reason",
    "reminder_count",
    "last_reminder_at"
]

VALID_STATUSES = [
    "Pending Approval",
    "Approved",
    "Rejected",
    "Duplicate",
    "Low Confidence",
    "Failed"
]

VALID_SOURCES = ["Gmail", "Drive"]


def validate_invoice_row(row: Dict[str, Any]) -> List[str]:
    """Validate invoice row, return list of errors (empty if valid)."""
    errors = []
    
    # Check required fields
    for field in REQUIRED_FIELDS:
        if field not in row:
            errors.append(f"Missing required field: {field}")
        elif row[field] is None and field not in ["approved_at", "approved_by", "rejected_at", "reject_reason"]:
            errors.append(f"Required field is None: {field}")
    
    # Validate status
    if "status" in row and row["status"] not in VALID_STATUSES:
        errors.append(f"Invalid status: {row['status']}. Must be one of {VALID_STATUSES}")
    
    # Validate source
    if "source" in row and row["source"] not in VALID_SOURCES:
        errors.append(f"Invalid source: {row['source']}. Must be one of {VALID_SOURCES}")
    
    # Validate amount is numeric
    if "amount" in row and row["amount"] is not None:
        try:
            amt = float(row["amount"])
        except (ValueError, TypeError):
            errors.append(f"Amount must be numeric: {row['amount']}")
        else:
            # BUG #3 fix: reject negative amounts
            if amt < 0:
                errors.append(f"Amount must be positive: {row['amount']}")
    
    # Validate confidence is 0-1
    if "confidence" in row and row["confidence"] is not None:
        try:
            conf = float(row["confidence"])
            if not (0 <= conf <= 1):
                errors.append(f"Confidence must be 0-1: {conf}")
        except (ValueError, TypeError):
            errors.append(f"Confidence must be numeric: {row['confidence']}")
    
    # Validate dates are ISO format (basic check)
    date_fields = ["received_at", "invoice_date", "approved_at", "rejected_at", "created_at", "updated_at", "last_reminder_at"]
    for field in date_fields:
        if field in row and row[field]:
            try:
                datetime.fromisoformat(str(row[field]).replace("Z", "+00:00"))
            except (ValueError, AttributeError):
                errors.append(f"Invalid date format for {field}: {row[field]} (expected ISO 8601)")
    
    # Validate reminder_count is non-negative integer
    if "reminder_count" in row and row["reminder_count"] is not None:
        try:
            count = int(row["reminder_count"])
            if count < 0:
                errors.append(f"reminder_count must be >= 0: {count}")
        except (ValueError, TypeError):
            errors.append(f"reminder_count must be integer: {row['reminder_count']}")
    
    return errors


def create_valid_invoice_row(**overrides) -> Dict[str, Any]:
    """Create a valid invoice row for testing."""
    base = {
        "invoice_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
        "received_at": "2026-08-12T14:30:00+07:00",
        "vendor": "PT Sumber Makmur",
        "invoice_date": "2026-08-10",
        "invoice_number": "INV-2026-00123",
        "amount": 15000000,
        "status": "Pending Approval",
        "confidence": 0.94,
        "drive_file_id": "1AbCdefGhIjKlMnOpQrStUvWxYz",
        "drive_file_link": "https://drive.google.com/file/d/1AbCdefGhIjKlMnOpQrStUvWxYz/view",
        "source": "Gmail",
        "approved_at": None,
        "approved_by": None,
        "rejected_at": None,
        "reject_reason": None,
        "reminder_count": 0,
        "last_reminder_at": None,
        "created_at": "2026-08-12T14:30:00+07:00",
        "updated_at": "2026-08-12T14:30:00+07:00"
    }
    base.update(overrides)
    return base


class TestSheetsSchema:
    
    def test_valid_row_passes(self):
        row = create_valid_invoice_row()
        errors = validate_invoice_row(row)
        assert errors == []
    
    def test_missing_required_field_fails(self):
        row = create_valid_invoice_row()
        del row["vendor"]
        errors = validate_invoice_row(row)
        assert any("Missing required field: vendor" in e for e in errors)
    
    def test_invalid_status_fails(self):
        row = create_valid_invoice_row(status="Invalid Status")
        errors = validate_invoice_row(row)
        assert any("Invalid status" in e for e in errors)
    
    def test_all_valid_statuses_pass(self):
        for status in VALID_STATUSES:
            row = create_valid_invoice_row(status=status)
            errors = validate_invoice_row(row)
            assert not any("Invalid status" in e for e in errors), f"Status {status} failed: {errors}"
    
    def test_invalid_source_fails(self):
        row = create_valid_invoice_row(source="WhatsApp")
        errors = validate_invoice_row(row)
        assert any("Invalid source" in e for e in errors)
    
    def test_non_numeric_amount_fails(self):
        row = create_valid_invoice_row(amount="fifteen million")
        errors = validate_invoice_row(row)
        assert any("Amount must be numeric" in e for e in errors)
    
    def test_confidence_out_of_range_fails(self):
        row = create_valid_invoice_row(confidence=1.5)
        errors = validate_invoice_row(row)
        assert any("Confidence must be 0-1" in e for e in errors)
    
    def test_negative_confidence_fails(self):
        row = create_valid_invoice_row(confidence=-0.1)
        errors = validate_invoice_row(row)
        assert any("Confidence must be 0-1" in e for e in errors)
    
    def test_invalid_date_format_fails(self):
        row = create_valid_invoice_row(invoice_date="10/08/2026")
        errors = validate_invoice_row(row)
        assert any("Invalid date format" in e for e in errors)
    
    def test_valid_iso_dates_pass(self):
        row = create_valid_invoice_row(
            received_at="2026-08-12T14:30:00+07:00",
            invoice_date="2026-08-10",
            approved_at="2026-08-12T14:45:00+07:00",
            created_at="2026-08-12T14:30:00+07:00",
            updated_at="2026-08-12T14:45:00+07:00"
        )
        errors = validate_invoice_row(row)
        assert not any("Invalid date format" in e for e in errors)
    
    def test_negative_reminder_count_fails(self):
        row = create_valid_invoice_row(reminder_count=-1)
        errors = validate_invoice_row(row)
        assert any("reminder_count must be >=" in e for e in errors)
    
    def test_negative_amount_fails(self):
        row = create_valid_invoice_row(amount=-5000000)
        errors = validate_invoice_row(row)
        assert any("Amount must be positive" in e for e in errors)

    def test_optional_fields_can_be_none(self):
        row = create_valid_invoice_row(
            approved_at=None,
            approved_by=None,
            rejected_at=None,
            reject_reason=None,
            last_reminder_at=None
        )
        errors = validate_invoice_row(row)
        # These fields are allowed to be None
        assert not any("Missing required field" in e and f in e for e in errors for f in ["approved_at", "approved_by", "rejected_at", "reject_reason", "last_reminder_at"])


if __name__ == "__main__":
    pytest.main([__file__, "-v"])