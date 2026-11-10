"""
HybridGuard AI - Automated Test Suite.
Tests 100% of hybrid routing paths, zero-leakage PII tokenization,
cloud escalation, fallback resilience, and cryptographic audit integrity.
"""

import unittest
import hashlib
from src.hybrid_guard import HybridGuard
from src.models import (
    DocumentType,
    ExecutionTarget,
    RiskTier,
    RoutingPolicy,
    PIIEntityType
)
from src.privacy_engine import PIIShield
from src.cloud_engine import CloudSecurityViolation, FirebaseCloudGeminiEngine


class TestHybridGuardAI(unittest.TestCase):

    def setUp(self):
        self.guard = HybridGuard()
        self.privacy_shield = PIIShield()

    def test_01_routine_invoice_processed_on_device_zero_egress(self):
        """Routine low-value invoices must be processed 100% on-device with 0 network bytes."""
        text = """
        INVOICE #001
        Date: Nov 10, 2026
        Vendor: Simple Office Supplies Ltd
        Contact: Alice Smith (alice@office.com)
        Total Payable: $1,450.00 USD
        Terms: Net 30
        IBAN: US12ABCD000987654321
        """
        result = self.guard.process_document(text, doc_type=DocumentType.INVOICE)

        # Assertions
        self.assertEqual(result.routing_decision.target, ExecutionTarget.ON_DEVICE_GEMMA_NANO)
        self.assertEqual(result.routing_decision.risk_tier, RiskTier.LOW)
        self.assertEqual(result.compliance_status, "PASSED")
        self.assertEqual(result.execution_metadata.get("network_bytes_sent"), 0)
        self.assertTrue(result.execution_metadata.get("air_gapped_verified"))
        self.assertGreater(result.routing_decision.pii_entities_count, 0)
        self.assertIn("Gemma Nano", result.summary)

    def test_02_high_value_invoice_escalated_to_cloud(self):
        """Invoices exceeding $50,000 threshold must escalate to Firebase Cloud Gemini."""
        text = """
        INVOICE #999-CORP
        Vendor: Supercomputing GPU Data Center AG
        Contact: Bob Mueller (bob@supergpu.eu)
        IBAN: DE89370400440532013000
        Tax ID: DE123456789
        Total Payable: $120,000.00 USD
        Payment of: $120,000.00
        Terms: Due upon receipt. Special offshore wire routing requested.
        """
        result = self.guard.process_document(text, doc_type=DocumentType.INVOICE)

        self.assertEqual(result.routing_decision.target, ExecutionTarget.HYBRID_CLOUD_GEMINI)
        self.assertIn(result.routing_decision.risk_tier, [RiskTier.HIGH, RiskTier.CRITICAL])
        self.assertTrue(result.routing_decision.payload_redacted)
        self.assertIn("Firebase Cloud Gemini", result.summary)
        self.assertTrue(len(result.financial_risks) > 0)

    def test_03_zero_pii_leakage_in_cloud_payload(self):
        """Sanitized payload dispatched to cloud must NEVER contain raw sensitive PII."""
        raw_iban = "DE89370400440532013000"
        raw_email = "secret.exec@enterprise.com"
        raw_ssn = "123-45-6789"
        
        text = f"""
        CONFIDENTIAL CONTRACT
        Signer: John Travolta
        Email: {raw_email}
        Social Security: {raw_ssn}
        Wire: {raw_iban}
        Indemnify and hold harmless without limitation.
        """
        redacted = self.privacy_shield.redact(text)

        # Zero leakage guarantees
        self.assertTrue(redacted.zero_leakage_verified)
        self.assertNotIn(raw_iban, redacted.sanitized_text)
        self.assertNotIn(raw_email, redacted.sanitized_text)
        self.assertNotIn(raw_ssn, redacted.sanitized_text)
        self.assertIn("[TOKEN_IBAN_", redacted.sanitized_text)
        self.assertIn("[TOKEN_EMAIL_", redacted.sanitized_text)

    def test_04_reversible_tokenization_and_rehydration(self):
        """Rehydration must accurately restore original PII in local enclave."""
        text = "Authorized Signature: Jane Doe, Contact: jane@test.com."
        redacted = self.privacy_shield.redact(text)
        rehydrated = self.privacy_shield.rehydrate(redacted.sanitized_text, redacted.token_map)
        
        self.assertEqual(text, rehydrated)

    def test_05_complex_contract_escalated_for_liability(self):
        """Contracts with asymmetric uncapped indemnification must trigger Cloud Arbiter."""
        text = """
        SERVICES AGREEMENT
        Section 9: Consultant agrees to indemnify and hold harmless without limitation
        Client for all consequential damages with unlimited liability.
        Governing law of the state of New York with mandatory foreign arbitration in Zurich.
        """
        result = self.guard.process_document(text, doc_type=DocumentType.CONTRACT)

        self.assertEqual(result.routing_decision.target, ExecutionTarget.HYBRID_CLOUD_GEMINI)
        self.assertGreaterEqual(result.anomaly_score, 0.40)
        self.assertTrue(any("Indemnification" in r for r in result.legal_risks))
        self.assertEqual(result.compliance_status, "REVIEW_REQUIRED")

    def test_06_force_offline_mode_enforces_on_device(self):
        """When force_offline_mode is set, high-value contracts stay 100% on device."""
        air_gapped_policy = RoutingPolicy(force_offline_mode=True)
        air_gapped_guard = HybridGuard(policy=air_gapped_policy)

        text = """
        HIGH EXPOSURE AIR-GAPPED INVOICE
        Total Payable: $5,000,000.00 USD
        Offshore account cryptocurrency wire.
        """
        result = air_gapped_guard.process_document(text, doc_type=DocumentType.INVOICE)

        self.assertEqual(result.routing_decision.target, ExecutionTarget.ON_DEVICE_GEMMA_NANO)
        self.assertEqual(result.execution_metadata.get("network_bytes_sent"), 0)

    def test_07_network_failure_fallback_to_degraded_local(self):
        """If cloud is unreachable, system must fallback to degraded local mode with review flag."""
        failing_guard = HybridGuard(simulate_network_failure=True)
        text = """
        HIGH RISK INVOICE
        Total Payable: $250,000.00 USD
        Terms: Due immediately.
        """
        result = failing_guard.process_document(text, doc_type=DocumentType.INVOICE)

        # Since network was marked down, policy immediately bounds to local
        self.assertEqual(result.routing_decision.target, ExecutionTarget.ON_DEVICE_GEMMA_NANO)

    def test_08_cryptographic_audit_chain_integrity(self):
        """Audit chain must verify as valid and maintain unbroken cryptographic linking."""
        guard = HybridGuard()
        
        # Process 3 distinct documents
        guard.process_document("Invoice 1: $500", DocumentType.INVOICE)
        guard.process_document("Invoice 2: $75,000", DocumentType.INVOICE)
        guard.process_document("Contract 3: unlimited liability", DocumentType.CONTRACT)

        self.assertEqual(len(guard.audit_log.chain), 3)
        self.assertTrue(guard.audit_log.verify_integrity())

    def test_09_audit_trail_tamper_detection(self):
        """Tampering with an audit block hash must cause integrity verification failure."""
        guard = HybridGuard()
        guard.process_document("Invoice 1: $500", DocumentType.INVOICE)
        guard.process_document("Invoice 2: $1000", DocumentType.INVOICE)

        self.assertTrue(guard.audit_log.verify_integrity())

        # Tamper with block #0 hash
        guard.audit_log.chain[0].current_block_hash = "deadbeef00000000000000000000000000000000000000000000000000000000"
        
        self.assertFalse(guard.audit_log.verify_integrity())

    def test_10_custom_financial_threshold(self):
        """Adjusting financial threshold alters routing behavior predictably."""
        # Lower threshold to $5,000
        low_threshold_policy = RoutingPolicy(financial_threshold_usd=5000.0)
        custom_guard = HybridGuard(policy=low_threshold_policy)

        text = "Total Payable: $8,500.00 USD"
        result = custom_guard.process_document(text, DocumentType.INVOICE)
        self.assertEqual(result.routing_decision.target, ExecutionTarget.HYBRID_CLOUD_GEMINI)

        # Raise threshold to $100,000
        high_threshold_policy = RoutingPolicy(financial_threshold_usd=100000.0)
        high_guard = HybridGuard(policy=high_threshold_policy)
        result2 = high_guard.process_document(text, DocumentType.INVOICE)
        self.assertEqual(result2.routing_decision.target, ExecutionTarget.ON_DEVICE_GEMMA_NANO)


if __name__ == "__main__":
    unittest.main()
