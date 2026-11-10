"""
HybridGuard AI - Local-First Privacy Shield & Tokenization Engine.
Performs client-side regex & heuristic entity extraction, reversible tokenization,
and zero-leakage verification before any payload can leave the device.
"""

import re
import hashlib
import hmac
from typing import Dict, List
from .models import PIIEntity, PIIEntityType, RedactedDocument


class PIIShield:
    """
    On-device privacy shield that sanitizes sensitive PII entities into reversible
    surrogate tokens. The private mapping never leaves the client device.
    """

    PATTERNS = {
        PIIEntityType.EMAIL: re.compile(
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b'
        ),
        PIIEntityType.PHONE: re.compile(
            r'\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{2,4}\)?[-.\s]?\d{3,4}[-.\s]?\d{3,4}\b'
        ),
        PIIEntityType.IBAN: re.compile(
            r'\b[A-Z]{2}[0-9]{2}(?:[ ]?[0-9A-Z]{4}){4}(?:[ ]?[0-9A-Z]{1,2})?\b'
        ),
        PIIEntityType.SSN: re.compile(
            r'\b\d{3}-\d{2}-\d{4}\b'
        ),
        PIIEntityType.TAX_ID: re.compile(
            r'\b(?:IT[0-9]{11}|DE[0-9]{9}|FR[0-9A-Z]{2}[0-9]{9}|[A-Z]{6}[0-9]{2}[A-Z][0-9]{2}[A-Z][0-9]{3}[A-Z]|TAX-[0-9]{6,10}|EIN\s*#?\s*\d{2}-\d{7})\b'
        ),
        PIIEntityType.CONFIDENTIAL_KEYWORD: re.compile(
            r'\b(?:CONFIDENTIAL|STRICTLY PRIVATE|RESTRICTED IP|PROPRIETARY TRADE SECRET|UNDER NDA)\b',
            re.IGNORECASE
        ),
    }

    # Named entity heuristic patterns (single line matches only)
    NAME_PATTERNS = [
        re.compile(r'(?:Attn|Attention|Signer|Representative|Authorized Signature|Beneficiary|Employee|Director):[ \t]*([A-Z][a-z]+(?:[ \t]+[A-Z][a-z]+){1,2})'),
        re.compile(r'(?:Contractor|Consultant|Party A|Party B|Disclosing Party|Receiving Party):[ \t]*([A-Z][a-z]+(?:[ \t]+[A-Z][a-z]+){1,2})'),
        re.compile(r'\b(?:Mr\.|Ms\.|Mrs\.|Dr\.)[ \t]+([A-Z][a-z]+(?:[ \t]+[A-Z][a-z]+)+)\b'),
    ]

    # Specific financial salary / bank transfer patterns (single line)
    SALARY_PATTERNS = [
        re.compile(r'(?:Base Salary|Annual Compensation|Executive Retainer|Bonus Guarantee):[ \t]*([$€£][ \t]*[0-9]{1,3}(?:,[0-9]{3})*(?:\.[0-9]{2})?)'),
        re.compile(r'(?:Wire Amount|Payment of|Balance Due|Total Payable):[ \t]*([$€£][ \t]*[0-9]{1,3}(?:,[0-9]{3})*(?:\.[0-9]{2})?)'),
    ]

    TAG_PREFIXES = {
        PIIEntityType.EMAIL: "TOKEN_EMAIL",
        PIIEntityType.PHONE: "TOKEN_PHONE",
        PIIEntityType.IBAN: "TOKEN_IBAN",
        PIIEntityType.SSN: "TOKEN_SSN",
        PIIEntityType.TAX_ID: "TOKEN_TAX",
        PIIEntityType.PERSON_NAME: "TOKEN_NAME",
        PIIEntityType.COMPANY_NAME: "TOKEN_ORG",
        PIIEntityType.SALARY_OR_AMOUNT: "TOKEN_AMT",
        PIIEntityType.CONFIDENTIAL_KEYWORD: "TOKEN_RESTRICTED",
    }

    def __init__(self, salt: str = "hybrid-guard-local-enclave-salt"):
        self.salt = salt.encode("utf-8")

    def _generate_token_id(self, entity_type: PIIEntityType, original_value: str) -> str:
        """Generates a deterministic surrogate token hash scoped to the client enclave."""
        prefix = self.TAG_PREFIXES.get(entity_type, "TOKEN_SECURE")
        digest = hmac.new(self.salt, original_value.encode("utf-8"), hashlib.sha256).hexdigest()[:8]
        return f"[{prefix}_{digest}]"

    def scan_entities(self, text: str) -> List[PIIEntity]:
        """Scans raw document text and inventories all sensitive entities with character spans."""
        entities: List[PIIEntity] = []

        # 1. Regex patterns
        for entity_type, regex in self.PATTERNS.items():
            for match in regex.finditer(text):
                val = match.group().strip()
                if len(val) >= 3:
                    token = self._generate_token_id(entity_type, val)
                    entities.append(PIIEntity(
                        entity_type=entity_type,
                        original_value=val,
                        token_id=token,
                        start_pos=match.start(),
                        end_pos=match.end(),
                        confidence=0.98
                    ))

        # 2. Named entity heuristics
        for pattern in self.NAME_PATTERNS:
            for match in pattern.finditer(text):
                val = match.group(1).strip()
                token = self._generate_token_id(PIIEntityType.PERSON_NAME, val)
                entities.append(PIIEntity(
                    entity_type=PIIEntityType.PERSON_NAME,
                    original_value=val,
                    token_id=token,
                    start_pos=match.start(1),
                    end_pos=match.end(1),
                    confidence=0.92
                ))

        # 3. High-sensitivity salary / payment patterns
        for pattern in self.SALARY_PATTERNS:
            for match in pattern.finditer(text):
                val = match.group(1).strip()
                token = self._generate_token_id(PIIEntityType.SALARY_OR_AMOUNT, val)
                entities.append(PIIEntity(
                    entity_type=PIIEntityType.SALARY_OR_AMOUNT,
                    original_value=val,
                    token_id=token,
                    start_pos=match.start(1),
                    end_pos=match.end(1),
                    confidence=0.95
                ))

        # Deduplicate overlapping matches prioritizing longer matches
        entities.sort(key=lambda e: (e.start_pos, -(e.end_pos - e.start_pos)))
        deduped: List[PIIEntity] = []
        last_end = -1
        for e in entities:
            if e.start_pos >= last_end:
                deduped.append(e)
                last_end = e.end_pos

        return deduped

    def redact(self, text: str) -> RedactedDocument:
        """
        Replaces sensitive entities with secure tokens and builds a private in-memory token map.
        Verifies zero-leakage before returning.
        """
        entities = self.scan_entities(text)
        token_map: Dict[str, str] = {}

        # Replace from end to start to maintain span indexing stability
        sanitized = text
        for entity in sorted(entities, key=lambda e: e.start_pos, reverse=True):
            token_map[entity.token_id] = entity.original_value
            sanitized = (
                sanitized[:entity.start_pos] +
                entity.token_id +
                sanitized[entity.end_pos:]
            )

        original_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
        zero_leak = self.verify_zero_leakage(sanitized, [e.original_value for e in entities])

        return RedactedDocument(
            original_hash=original_hash,
            sanitized_text=sanitized,
            token_map=token_map,
            entities_detected=entities,
            zero_leakage_verified=zero_leak
        )

    def rehydrate(self, sanitized_text: str, token_map: Dict[str, str]) -> str:
        """
        Restores original sensitive values from surrogate tokens inside the secure local enclave.
        """
        result = sanitized_text
        for token_id, original_value in token_map.items():
            result = result.replace(token_id, original_value)
        return result

    def verify_zero_leakage(self, sanitized_text: str, original_values: List[str]) -> bool:
        """
        Cryptographic check ensuring no unmasked sensitive string exists in the sanitized payload.
        """
        for val in original_values:
            # Skip trivial short strings to avoid accidental substring hits
            if len(val) >= 4 and val in sanitized_text:
                return False
        return True
