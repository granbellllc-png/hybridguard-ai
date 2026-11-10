"""
HybridGuard AI - Core Domain Models & Schemas.
Defines schemas for documents, routing decisions, privacy tokens,
and cryptographic audit trails across On-Device and Firebase Cloud tiers.
"""

from enum import Enum
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field
import time
import uuid


class DocumentType(str, Enum):
    INVOICE = "INVOICE"
    CONTRACT = "CONTRACT"
    NDA = "NDA"
    FINANCIAL_REPORT = "FINANCIAL_REPORT"
    SENSITIVE_MEMO = "SENSITIVE_MEMO"


class RiskTier(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class ExecutionTarget(str, Enum):
    ON_DEVICE_GEMMA_NANO = "ON_DEVICE_GEMMA_NANO"
    HYBRID_CLOUD_GEMINI = "HYBRID_CLOUD_GEMINI"
    FALLBACK_LOCAL_DEGRADED = "FALLBACK_LOCAL_DEGRADED"


class PIIEntityType(str, Enum):
    IBAN = "IBAN"
    TAX_ID = "TAX_ID"
    SSN = "SSN"
    PERSON_NAME = "PERSON_NAME"
    COMPANY_NAME = "COMPANY_NAME"
    EMAIL = "EMAIL"
    PHONE = "PHONE"
    SALARY_OR_AMOUNT = "SALARY_OR_AMOUNT"
    CONFIDENTIAL_KEYWORD = "CONFIDENTIAL_KEYWORD"


class PIIEntity(BaseModel):
    entity_type: PIIEntityType
    original_value: str
    token_id: str
    start_pos: int
    end_pos: int
    confidence: float = 1.0


class RedactedDocument(BaseModel):
    original_hash: str
    sanitized_text: str
    token_map: Dict[str, str] = Field(default_factory=dict, description="Secure client-side only mapping: token_id -> original_value")
    entities_detected: List[PIIEntity] = Field(default_factory=list)
    redaction_timestamp: float = Field(default_factory=time.time)
    zero_leakage_verified: bool = False


class RoutingPolicy(BaseModel):
    financial_threshold_usd: float = Field(default=50000.0, description="Amount above which Cloud financial arbiter is triggered")
    legal_complexity_threshold: float = Field(default=0.65, description="Complexity score threshold for Cloud escalation")
    anomaly_threshold: float = Field(default=0.60, description="Anomaly score threshold for Cloud escalation")
    force_offline_mode: bool = Field(default=False, description="Enforce 100% on-device local execution (air-gapped)")
    max_cloud_latency_ms: int = Field(default=3500, description="Max allowed cloud response latency before fallback")
    allow_cloud_escalation: bool = Field(default=True, description="Master switch for Firebase AI Logic Cloud")


class RoutingDecision(BaseModel):
    decision_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    target: ExecutionTarget
    risk_tier: RiskTier
    reasons: List[str] = Field(default_factory=list)
    pii_entities_count: int = 0
    payload_redacted: bool = False
    confidence: float = 1.0
    evaluated_at: float = Field(default_factory=time.time)


class AnalysisResult(BaseModel):
    document_id: str
    document_type: DocumentType
    routing_decision: RoutingDecision
    summary: str
    financial_risks: List[str] = Field(default_factory=list)
    legal_risks: List[str] = Field(default_factory=list)
    anomaly_score: float = 0.0
    detected_amount_usd: Optional[float] = None
    detected_currency: Optional[str] = None
    compliance_status: str = "PASSED"  # PASSED, REVIEW_REQUIRED, REJECTED
    actionable_recommendations: List[str] = Field(default_factory=list)
    execution_metadata: Dict[str, Any] = Field(default_factory=dict)
    privacy_attestation: Dict[str, Any] = Field(default_factory=dict)
