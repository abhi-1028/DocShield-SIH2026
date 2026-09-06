import subprocess
import sys


# ============================================================
# DOCSHIELD - COMPLETE DOCUMENT PROTECTION PIPELINE
# ============================================================


def run_step(
    filename,
    description
):

    print()
    print("=" * 60)
    print(description)
    print("=" * 60)
    print()


    result = subprocess.run(
        [
            sys.executable,
            filename
        ]
    )


    if result.returncode != 0:

        print()
        print(
            f"ERROR: {filename} failed."
        )

        print(
            f"Return code: {result.returncode}"
        )

        print()

        return False


    return True


# ============================================================
# START
# ============================================================

print()
print("=" * 60)
print("DOCSHIELD - AI DOCUMENT PROTECTION SYSTEM")
print("=" * 60)

print()
print(
    "Starting complete document protection pipeline..."
)


# ============================================================
# STEP 1
# ============================================================

if not run_step(
    "preprocess.py",
    "STEP 1 - DOCUMENT PREPROCESSING"
):

    exit(1)


# ============================================================
# STEP 2
# ============================================================

if not run_step(
    "perspective.py",
    "STEP 2 - PERSPECTIVE CORRECTION"
):

    exit(1)


# ============================================================
# STEP 3
# ============================================================

if not run_step(
    "ocr.py",
    "STEP 3 - OCR TEXT EXTRACTION"
):

    exit(1)


# ============================================================
# STEP 4
# ============================================================

if not run_step(
    "detector.py",
    "STEP 4 - SENSITIVE DATA DETECTION"
):

    exit(1)


# ============================================================
# STEP 5
# ============================================================

if not run_step(
    "visual_redactor.py",
    "STEP 5 - VISUAL REDACTION"
):

    exit(1)


# ============================================================
# COMPLETE
# ============================================================

print()
print("=" * 60)
print("DOCSHIELD PIPELINE COMPLETED SUCCESSFULLY!")
print("=" * 60)
print()

print(
    "Protected document:"
)

print(
    "sample/protected_document.png"
)

print()