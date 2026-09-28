"""Verification script for role-based PII/PHI de-identification and masking in SQL RAG."""
from __future__ import annotations

import os
import sys

# Ensure backend directory is in python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

from app.sql_rag.masking import (
    anonymize_patient_name,
    apply_role_masking,
    generalize_icd_code,
    mask_patient_name,
    mask_staff_name,
)
from app.sql_rag.chain import sql_rag_chain


def test_masking_unit():
    print("Testing unit masking functions...")
    
    # 1. Patient Name Masking
    assert mask_patient_name("Kavya Pillai") == "K**** P*****"
    assert mask_patient_name("Arjun Shetty") == "A**** S*****"
    assert mask_patient_name("A") == "A"
    assert mask_patient_name(None) == "[UNKNOWN]"
    assert anonymize_patient_name("Kavya Pillai") == "[ANONYMIZED]"
    
    # 2. Staff Name Masking
    assert mask_staff_name("Arjun Desai") == "Hospital Staff"
    
    # 3. ICD-10 Generalization
    assert generalize_icd_code("N17.9") == "N17"
    assert generalize_icd_code("I21.4") == "I21"
    
    # 4. apply_role_masking
    sample_rows = [
        {"claim_id": "CLM-2024-1000", "patient_name": "Kavya Pillai", "department": "nephrology", "claimed_amount": 72700.0},
        {"ticket_id": "TKT-2024-2000", "equipment_name": "SterilPro 3000", "raised_by": "Arjun Desai"},
    ]
    
    billing_masked = apply_role_masking(sample_rows, role="billing_executive")
    assert billing_masked[0]["patient_name"] == "K**** P*****"
    assert billing_masked[1]["raised_by"] == "Hospital Staff"
    
    admin_masked = apply_role_masking(sample_rows, role="admin")
    assert admin_masked[0]["patient_name"] == "[ANONYMIZED]"
    assert admin_masked[1]["raised_by"] == "Hospital Staff"

    print("✅ All unit masking tests passed!\n")


def test_chain_masking():
    print("Testing end-to-end SQL RAG chain with role-based masking...")
    question = "List the first 3 nephrology claims with patient names and claimed amounts."
    
    # Test as billing_executive
    print("\n--- Running as billing_executive ---")
    billing_ans = sql_rag_chain(question, role="billing_executive")
    print(f"Billing Executive Answer:\n{billing_ans}\n")
    
    # Raw name Kavya Pillai should NOT be in the answer
    assert "Kavya Pillai" not in billing_ans, "Raw patient name 'Kavya Pillai' leaked to billing_executive!"
    # Masked pattern should be present
    assert "K****" in billing_ans or "P*****" in billing_ans or "*" in billing_ans, "Masked asterisks expected in billing_ans!"
    print("✅ billing_executive receives masked patient names!")

    # Test as admin
    print("\n--- Running as admin ---")
    admin_ans = sql_rag_chain(question, role="admin")
    print(f"Admin Answer:\n{admin_ans}\n")
    
    assert "Kavya Pillai" not in admin_ans, "Raw patient name 'Kavya Pillai' leaked to admin!"
    assert "ANONYMIZED" in admin_ans or "[ANONYMIZED]" in admin_ans, "Expected [ANONYMIZED] in admin_ans!"
    print("✅ admin receives [ANONYMIZED] patient records!")


if __name__ == "__main__":
    test_masking_unit()
    test_chain_masking()
    print("\nALL ROLE-BASED MASKING VERIFICATION TESTS PASSED! 🎉")
