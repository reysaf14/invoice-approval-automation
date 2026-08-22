"""
Test OCR Extraction Logic
Tests for Google Document AI response parsing and field extraction.
"""

import json
import pytest
from typing import Dict, Any


def parse_doc_ai_response(response: Dict[str, Any]) -> Dict[str, Any]:
    """
    Parse Google Document AI response to extract invoice fields.
    Expected entities: vendor, invoice_date, invoice_number, amount
    """
    document = response.get("document", {})
    entities = document.get("entities", [])
    
    result = {
        "vendor": None,
        "invoice_date": None,
        "invoice_number": None,
        "amount": None,
        "confidence": {
            "vendor": 0.0,
            "invoice_date": 0.0,
            "invoice_number": 0.0,
            "amount": 0.0,
            "overall": 0.0
        }
    }
    
    entity_map = {
        "vendor": ["vendor", "supplier", "seller", "from"],
        "invoice_date": ["date", "invoice_date", "invoice date"],
        "invoice_number": ["invoice_number", "invoice_id", "number", "no"],
        "amount": ["amount", "total", "total_amount", "grand_total", "nominal"]
    }
    
    confidences = []
    
    for entity in entities:
        entity_type = entity.get("type", "").lower()
        mention_text = entity.get("mentionText", "").strip()
        confidence = entity.get("confidence", 0.0)
        
        for field, keywords in entity_map.items():
            if any(kw in entity_type for kw in keywords):
                result[field] = mention_text
                result["confidence"][field] = confidence
                confidences.append(confidence)
                break
    
    result["confidence"]["overall"] = sum(confidences) / len(confidences) if confidences else 0.0
    
    return result


def test_parse_doc_ai_response_basic():
    """Test parsing a typical Document AI response."""
    mock_response = {
        "document": {
            "entities": [
                {"type": "vendor", "mentionText": "PT Sumber Makmur", "confidence": 0.95},
                {"type": "invoice_date", "mentionText": "2026-08-10", "confidence": 0.98},
                {"type": "invoice_number", "mentionText": "INV-2026-00123", "confidence": 0.92},
                {"type": "total_amount", "mentionText": "15000000", "confidence": 0.97}
            ]
        }
    }
    
    result = parse_doc_ai_response(mock_response)
    
    assert result["vendor"] == "PT Sumber Makmur"
    assert result["invoice_date"] == "2026-08-10"
    assert result["invoice_number"] == "INV-2026-00123"
    assert result["amount"] == "15000000"
    assert result["confidence"]["overall"] > 0.9


def test_parse_doc_ai_response_missing_fields():
    """Test handling missing entities."""
    mock_response = {
        "document": {
            "entities": [
                {"type": "vendor", "mentionText": "CV Jaya Abadi", "confidence": 0.88},
                {"type": "invoice_number", "mentionText": "INV-001", "confidence": 0.85}
            ]
        }
    }
    
    result = parse_doc_ai_response(mock_response)
    
    assert result["vendor"] == "CV Jaya Abadi"
    assert result["invoice_number"] == "INV-001"
    assert result["invoice_date"] is None
    assert result["amount"] is None
    assert result["confidence"]["overall"] < 0.9


def test_confidence_threshold():
    """Test confidence threshold logic."""
    # Simulate low confidence extraction
    result = {
        "confidence": {
            "vendor": 0.70,
            "invoice_date": 0.60,
            "invoice_number": 0.80,
            "amount": 0.75,
            "overall": 0.71
        }
    }
    
    THRESHOLD = 0.85
    is_low_confidence = result["confidence"]["overall"] < THRESHOLD
    
    assert is_low_confidence == True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])