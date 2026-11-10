"""
HybridGuard AI - Hybrid Policy & Routing Engine.
Determines whether document processing remains 100% On-Device (Gemma Nano)
or escalates to Firebase Cloud (Gemini) based on financial thresholds, legal risk,
fraud anomaly scoring, and local device network/privacy constraints.
"""

from typing import Dict, Any, List
from .models import (
    DocumentType,
    RiskTier,
    ExecutionTarget,
    RoutingPolicy,
    RoutingDecision,
    RedactedDocument
)


class HybridPolicyEngine:
    """
    Arbitrates the boundary between edge inference and cloud escalation.
    Maximizes on-device execution to preserve privacy and reduce token costs,
    while escalating high-consequence decisions to cloud intelligence.
    """

    def __init__(self, policy: RoutingPolicy = None):
        self.policy = policy or RoutingPolicy()

    def evaluate_routing(
        self,
        doc_type: DocumentType,
        local_complexity: Dict[str, Any],
        redacted_doc: RedactedDocument,
        network_available: bool = True
    ) -> RoutingDecision:
        """
        Computes the optimal execution target based on multi-factor policy checks.
        """
        reasons: List[str] = []
        pii_count = len(redacted_doc.entities_detected)
        complexity_score = local_complexity.get("complexity_score", 0.0)
        financials = local_complexity.get("financials", {})
        amount = financials.get("amount") or 0.0

        # Rule 1: Air-gapped / Offline Force Mode
        if self.policy.force_offline_mode or not network_available:
            reasons.append("Air-Gapped / Offline constraint active: Routing 100% to On-Device Gemma Nano.")
            return RoutingDecision(
                target=ExecutionTarget.ON_DEVICE_GEMMA_NANO,
                risk_tier=RiskTier.LOW if complexity_score < 0.5 else RiskTier.MEDIUM,
                reasons=reasons,
                pii_entities_count=pii_count,
                payload_redacted=False,
                confidence=0.99
            )

        # Rule 2: Cloud escalation disallowed by policy
        if not self.policy.allow_cloud_escalation:
            reasons.append("Cloud escalation disabled by enterprise policy: Bound to On-Device inference.")
            return RoutingDecision(
                target=ExecutionTarget.ON_DEVICE_GEMMA_NANO,
                risk_tier=RiskTier.LOW,
                reasons=reasons,
                pii_entities_count=pii_count,
                payload_redacted=False,
                confidence=1.0
            )

        # Rule 3: High Financial Exposure Escalation
        financial_escalation = amount >= self.policy.financial_threshold_usd
        if financial_escalation:
            reasons.append(
                f"Financial Exposure Escalation: ${amount:,.2f} exceeds threshold "
                f"(${self.policy.financial_threshold_usd:,.2f}). Requires Firebase Cloud Financial Arbiter."
            )

        # Rule 4: Legal Clause Complexity Escalation
        legal_escalation = complexity_score >= self.policy.legal_complexity_threshold
        if legal_escalation:
            reasons.append(
                f"Legal Clause Complexity Escalation: Score {complexity_score:.2f} >= "
                f"threshold {self.policy.legal_complexity_threshold:.2f} (multi-jurisdiction / uncapped liability)."
            )

        # Rule 5: Severe Anomaly / Fraud Suspicion
        anomaly_escalation = complexity_score >= self.policy.anomaly_threshold
        if any("Severe Payment Anomaly" in ind for ind in local_complexity.get("indicators", [])):
            reasons.append("Fraud Indicator Detected: Non-standard disbursement method requires Cloud forensics.")
            anomaly_escalation = True

        # Synthesis
        if financial_escalation or legal_escalation or anomaly_escalation:
            risk = RiskTier.CRITICAL if anomaly_escalation else RiskTier.HIGH
            reasons.append(
                f"Local Privacy Shield engaged: {pii_count} PII entities will be shielded before cloud dispatch."
            )
            return RoutingDecision(
                target=ExecutionTarget.HYBRID_CLOUD_GEMINI,
                risk_tier=risk,
                reasons=reasons,
                pii_entities_count=pii_count,
                payload_redacted=True,
                confidence=0.96
            )

        # Default: Routine document handled completely on-device
        reasons.append(
            f"Routine document: Value (${amount:,.2f}) and legal complexity ({complexity_score:.2f}) "
            f"within autonomous on-device safety envelope."
        )
        return RoutingDecision(
            target=ExecutionTarget.ON_DEVICE_GEMMA_NANO,
            risk_tier=RiskTier.LOW,
            reasons=reasons,
            pii_entities_count=pii_count,
            payload_redacted=False,
            confidence=0.98
        )
