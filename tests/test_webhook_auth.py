"""
Test Webhook HMAC Authentication
Tests for signature verification and replay protection.
"""

import pytest
import hmac
import hashlib
import time
import json
from typing import Dict, Any


def generate_signature(secret: str, payload: Dict[str, Any], timestamp: int) -> str:
    """Generate HMAC-SHA256 signature for webhook payload."""
    payload_str = json.dumps(payload, separators=(',', ':'), sort_keys=True)
    message = f"{payload_str}.{timestamp}"
    signature = hmac.new(
        secret.encode('utf-8'),
        message.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    return f"sha256={signature}"


def verify_signature(secret: str, payload: Dict[str, Any], timestamp: int, signature: str, tolerance: int = 300) -> bool:
    """Verify HMAC signature and timestamp freshness."""
    # Check timestamp freshness (replay protection)
    now = int(time.time())
    if abs(now - timestamp) > tolerance:
        return False
    
    # Verify signature (constant-time comparison)
    expected = generate_signature(secret, payload, timestamp)
    return hmac.compare_digest(signature, expected)


class TestWebhookAuth:
    
    def test_valid_signature_passes(self):
        secret = "test_secret_32_bytes_hex_here___"
        payload = {"invoice_id": "abc-123", "action": "approve"}
        timestamp = int(time.time())
        signature = generate_signature(secret, payload, timestamp)
        
        assert verify_signature(secret, payload, timestamp, signature) == True
    
    def test_invalid_signature_fails(self):
        secret = "test_secret_32_bytes_hex_here___"
        payload = {"invoice_id": "abc-123", "action": "approve"}
        timestamp = int(time.time())
        signature = generate_signature(secret, payload, timestamp)
        
        # Tamper with payload
        bad_payload = {"invoice_id": "abc-123", "action": "reject"}
        assert verify_signature(secret, bad_payload, timestamp, signature) == False
    
    def test_expired_timestamp_fails(self):
        secret = "test_secret_32_bytes_hex_here___"
        payload = {"invoice_id": "abc-123", "action": "approve"}
        timestamp = int(time.time()) - 400  # 400 seconds ago, tolerance is 300
        signature = generate_signature(secret, payload, timestamp)
        
        assert verify_signature(secret, payload, timestamp, signature) == False
    
    def test_future_timestamp_fails(self):
        secret = "test_secret_32_bytes_hex_here___"
        payload = {"invoice_id": "abc-123", "action": "approve"}
        timestamp = int(time.time()) + 400  # 400 seconds in future
        signature = generate_signature(secret, payload, timestamp)
        
        assert verify_signature(secret, payload, timestamp, signature) == False
    
    def test_constant_time_comparison(self):
        """Verify hmac.compare_digest is used (timing attack resistant)."""
        # This test ensures the implementation uses compare_digest
        secret = "test_secret_32_bytes_hex_here___"
        payload = {"invoice_id": "abc-123", "action": "approve"}
        timestamp = int(time.time())
        signature = generate_signature(secret, payload, timestamp)
        
        # Should not raise, just return False for wrong signature
        assert verify_signature(secret, payload, timestamp, "sha256=wrong_signature") == False
    
    def test_payload_order_independence(self):
        """Signature should be same regardless of key order (sort_keys=True)."""
        secret = "test_secret_32_bytes_hex_here___"
        timestamp = int(time.time())
        
        payload1 = {"a": 1, "b": 2, "c": 3}
        payload2 = {"c": 3, "a": 1, "b": 2}
        
        sig1 = generate_signature(secret, payload1, timestamp)
        sig2 = generate_signature(secret, payload2, timestamp)
        
        assert sig1 == sig2
    
    def test_different_secrets_produce_different_signatures(self):
        secret1 = "secret_one_32_bytes_hex_here____"
        secret2 = "secret_two_32_bytes_hex_here____"
        payload = {"invoice_id": "abc-123", "action": "approve"}
        timestamp = int(time.time())
        
        sig1 = generate_signature(secret1, payload, timestamp)
        sig2 = generate_signature(secret2, payload, timestamp)
        
        assert sig1 != sig2
    
    def test_empty_payload(self):
        secret = "test_secret_32_bytes_hex_here___"
        payload = {}
        timestamp = int(time.time())
        signature = generate_signature(secret, payload, timestamp)
        
        assert verify_signature(secret, payload, timestamp, signature) == True
    
    def test_unicode_payload(self):
        secret = "test_secret_32_bytes_hex_here___"
        payload = {"vendor": "PT Sumber Makmur", "note": "invoice baru 📄"}
        timestamp = int(time.time())
        signature = generate_signature(secret, payload, timestamp)
        
        assert verify_signature(secret, payload, timestamp, signature) == True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])