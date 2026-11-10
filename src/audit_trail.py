"""
HybridGuard AI - Cryptographic Audit Trail & Merkle Ledger.
Maintains a tamper-evident chain of custody for all hybrid inference decisions,
ensuring verifiable proof of local privacy compliance and zero unauthorized cloud leakage.
"""

import hashlib
import json
import time
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from .models import AnalysisResult, ExecutionTarget


class AuditReceipt(BaseModel):
    block_index: int
    timestamp: float = Field(default_factory=time.time)
    document_id: str
    original_doc_hash: str
    target: ExecutionTarget
    pii_entities_count: int
    zero_leakage_verified: bool
    summary_digest: str
    previous_block_hash: str
    current_block_hash: str = ""


class CryptographicAuditLog:
    """
    Append-only cryptographically chained ledger of hybrid routing events.
    Verifiable by internal compliance officers and external privacy auditors.
    """

    GENESIS_HASH = "0000000000000000000000000000000000000000000000000000000000000000"

    def __init__(self):
        self.chain: List[AuditReceipt] = []

    def _compute_block_hash(
        self,
        block_index: int,
        timestamp: float,
        doc_id: str,
        doc_hash: str,
        target: str,
        pii_count: int,
        zero_leak: bool,
        summary_digest: str,
        prev_hash: str
    ) -> str:
        payload = (
            f"{block_index}|{timestamp:.4f}|{doc_id}|{doc_hash}|{target}|"
            f"{pii_count}|{zero_leak}|{summary_digest}|{prev_hash}"
        )
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def record_decision(
        self,
        analysis: AnalysisResult,
        original_text: str,
        zero_leakage_verified: bool
    ) -> AuditReceipt:
        """Appends a new cryptographically chained audit receipt."""
        block_index = len(self.chain)
        prev_hash = self.chain[-1].current_block_hash if self.chain else self.GENESIS_HASH
        timestamp = time.time()
        doc_hash = hashlib.sha256(original_text.encode("utf-8")).hexdigest()
        summary_digest = hashlib.sha256(analysis.summary.encode("utf-8")).hexdigest()[:16]
        target_str = analysis.routing_decision.target.value
        pii_count = analysis.routing_decision.pii_entities_count

        current_hash = self._compute_block_hash(
            block_index=block_index,
            timestamp=timestamp,
            doc_id=analysis.document_id,
            doc_hash=doc_hash,
            target=target_str,
            pii_count=pii_count,
            zero_leak=zero_leakage_verified,
            summary_digest=summary_digest,
            prev_hash=prev_hash
        )

        receipt = AuditReceipt(
            block_index=block_index,
            timestamp=timestamp,
            document_id=analysis.document_id,
            original_doc_hash=doc_hash,
            target=analysis.routing_decision.target,
            pii_entities_count=pii_count,
            zero_leakage_verified=zero_leakage_verified,
            summary_digest=summary_digest,
            previous_block_hash=prev_hash,
            current_block_hash=current_hash
        )

        self.chain.append(receipt)
        return receipt

    def verify_integrity(self) -> bool:
        """Verifies mathematical validity and unbroken hash linking of the entire audit chain."""
        if not self.chain:
            return True

        for i, receipt in enumerate(self.chain):
            expected_prev = self.chain[i - 1].current_block_hash if i > 0 else self.GENESIS_HASH
            if receipt.previous_block_hash != expected_prev:
                return False

            recalculated = self._compute_block_hash(
                block_index=receipt.block_index,
                timestamp=receipt.timestamp,
                doc_id=receipt.document_id,
                doc_hash=receipt.original_doc_hash,
                target=receipt.target.value,
                pii_count=receipt.pii_entities_count,
                zero_leak=receipt.zero_leakage_verified,
                summary_digest=receipt.summary_digest,
                prev_hash=receipt.previous_block_hash
            )
            if recalculated != receipt.current_block_hash:
                return False

        return True

    def export_ledger_json(self) -> str:
        """Exports ledger as serialized JSON string."""
        return json.dumps([r.model_dump() for r in self.chain], indent=2)
