"""
HybridGuard AI - Interactive CLI Demonstration.
Runs live benchmarks comparing pure on-device execution vs. hybrid cloud arbitration.
"""

import sys
import time
from .hybrid_guard import HybridGuard
from .models import DocumentType, RoutingPolicy, ExecutionTarget


# Sample test documents representing real-world enterprise scenarios
SAMPLE_DOCUMENTS = {
    "routine_invoice": {
        "type": DocumentType.INVOICE,
        "text": """
        INVOICE #INV-2026-4401
        Date: November 10, 2026
        Vendor: Acme Office Supplies LLC
        Contact: Jane Doe (email: jane.doe@acme-supplies.com, phone: +1-555-0199)
        Tax ID: EIN 12-3456789
        Client: Big4 Global Corp
        
        Item 1: Ergonomic Standing Desks (x4) - $2,400.00
        Item 2: Monitor Arms (x4) - $800.00
        Total Payable: $3,200.00 USD
        Terms: Standard Net 30
        Wire To: IBAN US89ACME00012345678901234
        """
    },
    "high_value_invoice": {
        "type": DocumentType.INVOICE,
        "text": """
        INVOICE #INV-CORP-9981
        Date: November 11, 2026
        Vendor: Apex Cloud Infrastructure GmbH
        Representative: Hans Gruber (Director)
        Email: h.gruber@apex-cloud.de
        Tax ID: DE123456789
        Bank Account: IBAN DE89370400440532013000
        
        Deliverable: High-Throughput H100 GPU Cluster Q4 Reserved Capacity
        Total Payable: $185,000.00 USD
        Payment of: $185,000.00
        Terms: Due upon receipt. Non-refundable.
        Note: Special offshore wire routing requested to Geneva intermediary account.
        """
    },
    "complex_contract": {
        "type": DocumentType.CONTRACT,
        "text": """
        MASTER SERVICES & IP AGREEMENT (STRICTLY PRIVATE UNDER NDA)
        Date: November 12, 2026
        Between: Big4 Sovereign AI Inc. and Global Synergy Partners LLC
        Signer: Michael Scott (Authorized Signature)
        Social Security: SSN 000-12-3456
        Executive Retainer: $95,000.00 per quarter.
        
        Section 8.1 - INDEMNIFICATION AND LIABILITY:
        Consultant agrees to indemnify and hold harmless without limitation Client against any third-party claims.
        Client shall bear unlimited liability for all consequential and punitive damages.
        
        Section 9.4 - INTELLECTUAL PROPERTY:
        Perpetual and irrevocable transfer of all intellectual property created during or prior to the engagement.
        
        Section 12.1 - GOVERNING LAW:
        Governing law of the state of New York with mandatory foreign arbitration in Zurich.
        """
    }
}


def run_interactive_demo():
    print("=" * 78)
    print("🛡️  HYBRIDGUARD AI: LOCAL-FIRST PRIVACY SHIELD & CLOUD FINANCIAL ARBITER")
    print("    Google Hackathon #BuildHybridAI 2026 — Firebase AI Logic Powered")
    print("=" * 78)

    guard = HybridGuard()

    for name, sample in SAMPLE_DOCUMENTS.items():
        print(f"\n>> PROCESSING SCENARIO: {name.upper().replace('_', ' ')}")
        print("-" * 78)
        
        start = time.perf_counter()
        result = guard.process_document(
            text=sample["text"],
            doc_type=sample["type"],
            document_id=f"demo-{name}"
        )
        elapsed = (time.perf_counter() - start) * 1000.0

        decision = result.routing_decision
        print(f"• Execution Target: {decision.target.value}")
        print(f"• Risk Tier:        {decision.risk_tier.value}")
        print(f"• Compliance:       {result.compliance_status}")
        print(f"• PII Shielded:     {decision.pii_entities_count} entities tokenized locally")
        print(f"• Anomaly Score:    {result.anomaly_score:.2f}")
        print(f"• Total Latency:    {elapsed:.1f}ms")
        print(f"• Summary:          {result.summary}")
        
        if result.financial_risks:
            print("• Financial Risks:")
            for fr in result.financial_risks:
                print(f"    - {fr}")

        if result.legal_risks:
            print("• Legal Risks:")
            for lr in result.legal_risks:
                print(f"    - {lr}")

        if result.actionable_recommendations:
            print("• Recommendations:")
            for rec in result.actionable_recommendations:
                print(f"    - {rec}")

        print(f"• Audit Block:      Index #{result.execution_metadata.get('audit_block_index')} | Hash: {result.execution_metadata.get('audit_block_hash')[:16]}...")

    # Verify audit chain integrity
    is_valid = guard.audit_log.verify_integrity()
    print("\n" + "=" * 78)
    print(f"🔐 Cryptographic Audit Ledger Integrity: {'100% VALID & UNBROKEN' if is_valid else 'CORRUPTED'}")
    print(f"📦 Total Blocks Chained: {len(guard.audit_log.chain)}")
    print("=" * 78)


if __name__ == "__main__":
    run_interactive_demo()
