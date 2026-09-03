import re

# OCR text
document_text = """
SAMPLE DOCUMENT
NOT A REAL DOCUMENT
Name: Rahul Kumar
ID: TEST-123456
DOB: 01/01/2000
This document is for testing only
"""

print("🛡️ Protecting sensitive information...")
print()

# Create a copy of the original text
protected_text = document_text

# Detect and replace Name
name_match = re.search(r"Name:\s*(.+)", protected_text)

if name_match:
    name = name_match.group(1).strip()
    masked_name = "*" * len(name)
    protected_text = protected_text.replace(name, masked_name)

# Detect and replace ID
id_match = re.search(r"ID:\s*(.+)", protected_text)

if id_match:
    document_id = id_match.group(1).strip()
    masked_id = "*" * len(document_id)
    protected_text = protected_text.replace(document_id, masked_id)

# Detect and replace Date of Birth
dob_match = re.search(r"DOB:\s*(\d{2}/\d{2}/\d{4})", protected_text)

if dob_match:
    dob = dob_match.group(1).strip()
    masked_dob = "*" * len(dob)
    protected_text = protected_text.replace(dob, masked_dob)


# Display protected document
print("===== PROTECTED DOCUMENT =====")
print()

print(protected_text)

print()
print("✅ Sensitive information protected!")