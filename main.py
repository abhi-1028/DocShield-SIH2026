import subprocess
import sys


def run_step(filename, description):

    print()
    print("=" * 60)
    print(description)
    print("=" * 60)
    print()

    # Use the exact Python interpreter running main.py
    result = subprocess.run(
        [sys.executable, filename]
    )

    if result.returncode != 0:

        print()
        print(f"❌ Error while running {filename}")
        print("🛑 Pipeline stopped.")

        sys.exit(1)


print()
print("🛡️ DOCSHIELD - AI DOCUMENT PROTECTION SYSTEM")
print()
print("Starting complete document protection pipeline...")


# Step 1 — Document preprocessing
run_step(
    "preprocess.py",
    "STEP 1 — DOCUMENT PREPROCESSING"
)


# Step 2 — Perspective correction
run_step(
    "perspective.py",
    "STEP 2 — PERSPECTIVE CORRECTION"
)


# Step 3 — OCR
run_step(
    "ocr.py",
    "STEP 3 — OCR TEXT EXTRACTION"
)


# Step 4 — Sensitive data detection
run_step(
    "detector.py",
    "STEP 4 — SENSITIVE DATA DETECTION"
)


# Step 5 — Visual redaction
run_step(
    "visual_redactor.py",
    "STEP 5 — VISUAL REDACTION"
)


print()
print("=" * 60)
print("🎉 DOCSHIELD PIPELINE COMPLETED SUCCESSFULLY!")
print("=" * 60)
print()
print("🔐 Protected document:")
print("sample/protected_document.png")
print()