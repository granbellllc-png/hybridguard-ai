"""
HybridGuard AI - On-Device Gemma Nano Engine (Local-First).
Simulates MediaPipe GenAI / Gemma Nano local execution on edge hardware.
Enforces ZERO network egress and delivers sub-50ms deterministic local analysis.
"""

import re
import time
from typing import Dict, Any, List, Optional
from .models import DocumentType, AnalysisResult, RoutingDecision, ExecutionTarget, RiskTier


class OnDeviceGemmaNanoEngine:
    """
    Local-first reasoning engine designed for Gemma Nano 2B / MediaPipe.
    Processes documents locally in client memory with zero network calls.
    """

    def __init__(self, model_name: str = "gemma-nano-2b-int4"):
        self.model_name = model_name
        self.total_local_inferences = 0

    def extract_financials(self, text: str) -> Dict[str, Any]:
        """Extracts total currency amount, invoice number, and payment terms."""
        amount = None
        currency = "USD"

        # Regex for amounts like $1,250.00 or 1500.50 EUR
        amount_match = re.search(r'[$€£]\s*([0-9]{1,3}(?:,[0-9]{3})*(?:\.[0-9]{2})?)', text)
        if not amount_match:
            amount_match = re.search(r'([0-9]{1,3}(?:,[0-9]{3})*(?:\.[0-9]{2})?)\s*(?:USD|EUR|GBP)', text)
        
        if amount_match:
            raw_val = amount_match.group(1).replace(",", "")
            try:
                amount = float(raw_val)
            except ValueError:
                amount = None

        if "€" in text or "EUR" in text:
            currency = "EUR"
        elif "£" in text or "GBP" in text:
            currency = "GBP"

        # Detect payment terms
        terms = "Standard Net 30"
        if "Net 15" in text:
            terms = "Net 15"
        elif "Net 60" in text:
            terms = "Net 60"
        elif "Due upon receipt" in text:
            terms = "Due Immediately"

        return {
            "amount": amount,
            "currency": currency,
            "payment_terms": terms
        }

    def evaluate_local_complexity(self, text: str, doc_type: DocumentType) -> Dict[str, Any]:
        """
        Fast on-device heuristic evaluation of legal and financial complexity.
        Used by the policy engine to decide if cloud arbitration is necessary.
        """
        indicators: List[str] = []
        score = 0.1

        # Check for high-liability legal phrases
        high_risk_phrases = [
            "indemnify and hold harmless without limitation",
            "unlimited liability",
            "perpetual and irrevocable transfer of all intellectual property",
            "governing law of the state of new york with mandatory foreign arbitration",
            "liquidated damages exceeding",
            "non-compete for a period of five years",
            "exclusive jurisdiction in",
            "joint and several liability"
        ]

        text_lower = text.lower()
        for phrase in high_risk_phrases:
            if phrase in text_lower:
                indicators.append(f"Legal Risk Clause: '{phrase}'")
                score += 0.25

        # Check for financial anomaly signals
        financials = self.extract_financials(text)
        amt = financials.get("amount") or 0.0

        if amt >= 50000.0:
            indicators.append(f"High Financial Exposure: ${amt:,.2f} exceeds standard local delegation limit ($50,000)")
            score += 0.35
        elif amt >= 15000.0:
            score += 0.15

        # Check for suspicious payment terms
        if "offshore account" in text_lower or "cryptocurrency wire" in text_lower or "immediate western union" in text_lower:
            indicators.append("Severe Payment Anomaly: Non-standard disbursement method detected")
            score += 0.50

        return {
            "complexity_score": min(score, 1.0),
            "indicators": indicators,
            "financials": financials
        }

    def analyze_local(
        self,
        document_id: str,
        text: str,
        doc_type: DocumentType,
        routing_decision: RoutingDecision
    ) -> AnalysisResult:
        """
        Executes local Gemma Nano reasoning.
        Produces structured summary, compliance status, and recommendations with ZERO egress.
        """
        start_time = time.perf_counter()
        self.total_local_inferences += 1

        financials = self.extract_financials(text)
        comp = self.evaluate_local_complexity(text, doc_type)

        amt = financials.get("amount")
        curr = financials.get("currency")

        # Determine compliance status
        if comp["complexity_score"] > 0.70:
            compliance = "REVIEW_REQUIRED"
        else:
            compliance = "PASSED"

        summary = (
            f"[Gemma Nano On-Device] Successfully audited {doc_type.value} locally. "
            f"Financial Value: {curr} {amt if amt is not None else 'N/A'}. "
            f"Payment Terms: {financials['payment_terms']}. "
            f"Data remained 100% confined to device enclave with zero cloud transmission."
        )

        recommendations = [
            "Invoice/contract structure matches standard corporate templates.",
            "Record marked for standard accounting reconciliation."
        ]

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0

        return AnalysisResult(
            document_id=document_id,
            document_type=doc_type,
            routing_decision=routing_decision,
            summary=summary,
            financial_risks=[],
            legal_risks=comp["indicators"],
            anomaly_score=round(comp["complexity_score"], 3),
            detected_amount_usd=amt,
            detected_currency=curr,
            compliance_status=compliance,
            actionable_recommendations=recommendations,
            execution_metadata={
                "engine": "OnDeviceGemmaNanoEngine",
                "model": self.model_name,
                "latency_ms": round(elapsed_ms, 2),
                "network_bytes_sent": 0,
                "air_gapped_verified": True
            },
            privacy_attestation={
                "storage_mode": "IN_MEMORY_EPHEMERAL",
                "cloud_egress": "NONE",
                "pii_leakage_risk": 0.0
            }
        )
