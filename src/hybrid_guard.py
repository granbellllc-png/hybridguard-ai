"""
HybridGuard AI - Core System Orchestrator.
Unites On-Device Privacy Shield, Policy Router, Firebase Cloud Arbiter,
and Cryptographic Audit Trail into a unified, enterprise-grade Hybrid AI pipeline.
"""

import uuid
import time
from typing import Optional, Dict, Any
from .models import (
    DocumentType,
    ExecutionTarget,
    RoutingPolicy,
    RoutingDecision,
    AnalysisResult,
    RiskTier
)
from .privacy_engine import PIIShield
from .on_device_engine import OnDeviceGemmaNanoEngine
from .cloud_engine import FirebaseCloudGeminiEngine, CloudSecurityViolation
from .policy_engine import HybridPolicyEngine
from .audit_trail import CryptographicAuditLog, AuditReceipt


class HybridGuard:
    """
    Main entry point for HybridGuard AI.
    Guarantees privacy-first local processing while dynamically unlocking
    Firebase AI Logic Cloud intelligence whenever warranted.
    """

    def __init__(
        self,
        policy: Optional[RoutingPolicy] = None,
        simulate_network_failure: bool = False
    ):
        self.policy = policy or RoutingPolicy()
        self.privacy_shield = PIIShield()
        self.local_engine = OnDeviceGemmaNanoEngine()
        self.cloud_engine = FirebaseCloudGeminiEngine()
        self.policy_engine = HybridPolicyEngine(self.policy)
        self.audit_log = CryptographicAuditLog()
        self.simulate_network_failure = simulate_network_failure

    def process_document(
        self,
        text: str,
        doc_type: DocumentType = DocumentType.INVOICE,
        document_id: Optional[str] = None
    ) -> AnalysisResult:
        """
        Executes end-to-end hybrid inference pipeline with privacy-first guarantees.
        """
        doc_id = document_id or f"doc-{uuid.uuid4().hex[:8]}"

        # Step 1: Local Privacy Shield Scan & Tokenization (On-Device)
        redacted_doc = self.privacy_shield.redact(text)

        # Step 2: Local Gemma Nano preliminary complexity & extraction (On-Device)
        local_complexity = self.local_engine.evaluate_local_complexity(text, doc_type)

        # Step 3: Policy Arbitration (On-Device)
        network_up = not self.simulate_network_failure
        routing_decision = self.policy_engine.evaluate_routing(
            doc_type=doc_type,
            local_complexity=local_complexity,
            redacted_doc=redacted_doc,
            network_available=network_up
        )

        # Step 4: Execution Routing
        if routing_decision.target == ExecutionTarget.ON_DEVICE_GEMMA_NANO:
            # 100% On-device execution - Zero cloud egress
            analysis = self.local_engine.analyze_local(
                document_id=doc_id,
                text=text,
                doc_type=doc_type,
                routing_decision=routing_decision
            )
            analysis.execution_metadata["pii_entities_shielded_locally"] = len(redacted_doc.entities_detected)

        elif routing_decision.target == ExecutionTarget.HYBRID_CLOUD_GEMINI:
            try:
                # Dispatch ONLY sanitized payload to Firebase Cloud Gemini
                cloud_analysis = self.cloud_engine.arbitrate(
                    document_id=doc_id,
                    redacted_doc=redacted_doc,
                    doc_type=doc_type,
                    routing_decision=routing_decision
                )

                # Step 4b: Secure Client-Side Enclave Rehydration
                # Restore original financial numbers / references locally for user presentation
                rehydrated_summary = self.privacy_shield.rehydrate(
                    cloud_analysis.summary,
                    redacted_doc.token_map
                )
                rehydrated_recommendations = [
                    self.privacy_shield.rehydrate(r, redacted_doc.token_map)
                    for r in cloud_analysis.actionable_recommendations
                ]

                # Extract local financials to populate detected amount
                financials = local_complexity.get("financials", {})

                analysis = AnalysisResult(
                    document_id=doc_id,
                    document_type=doc_type,
                    routing_decision=routing_decision,
                    summary=rehydrated_summary,
                    financial_risks=cloud_analysis.financial_risks,
                    legal_risks=cloud_analysis.legal_risks,
                    anomaly_score=cloud_analysis.anomaly_score,
                    detected_amount_usd=financials.get("amount"),
                    detected_currency=financials.get("currency"),
                    compliance_status=cloud_analysis.compliance_status,
                    actionable_recommendations=rehydrated_recommendations,
                    execution_metadata=cloud_analysis.execution_metadata,
                    privacy_attestation=cloud_analysis.privacy_attestation
                )

            except Exception as e:
                # Step 4c: Fallback Resiliency Engine
                # Fallback to local degraded analysis if cloud call fails
                fallback_decision = RoutingDecision(
                    target=ExecutionTarget.FALLBACK_LOCAL_DEGRADED,
                    risk_tier=RiskTier.HIGH,
                    reasons=[
                        f"Cloud Arbitration Failed or Unreachable: {str(e)}",
                        "Gracefully falling back to On-Device Gemma Nano with safety caveat."
                    ],
                    pii_entities_count=len(redacted_doc.entities_detected),
                    payload_redacted=False,
                    confidence=0.75
                )

                analysis = self.local_engine.analyze_local(
                    document_id=doc_id,
                    text=text,
                    doc_type=doc_type,
                    routing_decision=fallback_decision
                )
                analysis.compliance_status = "REVIEW_REQUIRED"
                analysis.actionable_recommendations.insert(
                    0,
                    "[CRITICAL FALLBACK] Cloud financial arbitration failed; manual executive sign-off required."
                )

        else:
            # Fallback path if target already set to degraded
            analysis = self.local_engine.analyze_local(
                document_id=doc_id,
                text=text,
                doc_type=doc_type,
                routing_decision=routing_decision
            )

        # Step 5: Cryptographic Audit Trail Chaining
        receipt = self.audit_log.record_decision(
            analysis=analysis,
            original_text=text,
            zero_leakage_verified=redacted_doc.zero_leakage_verified
        )
        analysis.execution_metadata["audit_block_index"] = receipt.block_index
        analysis.execution_metadata["audit_block_hash"] = receipt.current_block_hash

        return analysis
