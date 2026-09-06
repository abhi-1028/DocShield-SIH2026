import subprocess
import sys


# ============================================================
# DOCSHIELD - COMPLETE PIPELINE
# ============================================================

STEPS = [
    ("1. Document Preprocessing", "preprocess.py"),
    ("2. Perspective Correction", "perspective.py"),
    ("3. OCR", "ocr.py"),
    ("4. Sensitive Data Detection", "detector.py"),
    ("5. Visual Redaction", "visual_redactor.py"),
    ("6. Redaction Verification", "verify_redaction.py")
]


print("=" * 60)
print("              DOCSHIELD - SIH2026")
print("       AI DOCUMENT PROTECTION PIPELINE")
print("=" * 60)
print()


for step_name, script in STEPS:

    print()
    print("-" * 60)
    print(step_name)
    print(f"Running: {script}")
    print("-" * 60)
    print()

    result = subprocess.run(
        [sys.executable, script]
    )

    if result.returncode != 0:

        print()
        print("=" * 60)
        print(f"❌ PIPELINE FAILED")
        print(f"Failed at: {step_name}")
        print("=" * 60)

        sys.exit(1)


print()
print("=" * 60)
print("       DOCSHIELD PIPELINE COMPLETE ✅")
print("=" * 60)
print()
print("Protected document:")
print("sample/protected_document.png")
print()
print("Verification: PASSED ✅")
print("=" * 60)