"""
HybridGuard AI - Local-First Privacy Shield & Cloud Financial Arbiter.
Built with Firebase AI Logic (Gemma Nano On-Device + Gemini 2.5 Cloud).
"""

from .models import (
    DocumentType,
    RiskTier,
    ExecutionTarget,
    PIIEntityType,
    PIIEntity,
    RedactedDocument,
    RoutingPolicy,
    RoutingDecision,
    AnalysisResult
)
from .privacy_engine import PIIShield
from .on_device_engine import OnDeviceGemmaNanoEngine
from .cloud_engine import FirebaseCloudGeminiEngine, CloudSecurityViolation
from .policy_engine import HybridPolicyEngine
from .audit_trail import CryptographicAuditLog, AuditReceipt
from .hybrid_guard import HybridGuard

__version__ = "1.0.0"

__all__ = [
    "HybridGuard",
    "PIIShield",
    "OnDeviceGemmaNanoEngine",
    "FirebaseCloudGeminiEngine",
    "CloudSecurityViolation",
    "HybridPolicyEngine",
    "CryptographicAuditLog",
    "AuditReceipt",
    "DocumentType",
    "RiskTier",
    "ExecutionTarget",
    "PIIEntityType",
    "PIIEntity",
    "RedactedDocument",
    "RoutingPolicy",
    "RoutingDecision",
    "AnalysisResult"
]
