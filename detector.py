import json
import re

# Load OCR results
with open("ocr_results.json", "r", encoding="utf-8") as file:
    ocr_data = json.load(file)

print("🔍 Scanning OCR results for sensitive information...")
print()

# Store detected sensitive information
detected_data = []


# Check every OCR text line
for item in ocr_data:

    text = item["text"]


    # ---------------------------------------------
    # 1. Detect Name
    # ---------------------------------------------

    name_match = re.search(
        r"Name:\s*(.+)",
        text,
        re.IGNORECASE
    )

    if name_match:
        name = name_match.group(1).strip()

        detected_data.append({
            "type": "NAME",
            "value": name,
            "box": item["box"]
        })


    # ---------------------------------------------
    # 2. Detect ID
    # ---------------------------------------------

    id_match = re.search(
        r"ID:\s*(.+)",
        text,
        re.IGNORECASE
    )

    if id_match:
        document_id = id_match.group(1).strip()

        detected_data.append({
            "type": "ID",
            "value": document_id,
            "box": item["box"]
        })


    # ---------------------------------------------
    # 3. Detect Date of Birth
    # ---------------------------------------------

    dob_match = re.search(
        r"DOB:\s*(\d{2}/\d{2}/\d{4})",
        text,
        re.IGNORECASE
    )

    if dob_match:
        dob = dob_match.group(1).strip()

        detected_data.append({
            "type": "DATE OF BIRTH",
            "value": dob,
            "box": item["box"]
        })


    # ---------------------------------------------
    # 4. Detect Phone Number
    # ---------------------------------------------

    phone_match = re.search(
        r"\b(?:\+91[\s-]?)?[6-9]\d{9}\b",
        text
    )

    if phone_match:
        phone = phone_match.group(0).strip()

        detected_data.append({
            "type": "PHONE NUMBER",
            "value": phone,
            "box": item["box"]
        })


    # ---------------------------------------------
    # 5. Detect Email
    # ---------------------------------------------

    email_match = re.search(
        r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b",
        text
    )

    if email_match:
        email = email_match.group(0).strip()

        detected_data.append({
            "type": "EMAIL",
            "value": email,
            "box": item["box"]
        })


# ---------------------------------------------
# Display Results
# ---------------------------------------------

print("===== SENSITIVE INFORMATION DETECTED =====")
print()

if detected_data:

    for item in detected_data:

        print(
            f"🔴 {item['type']}: "
            f"{item['value']}"
        )

else:

    print("✅ No sensitive information detected.")


# ---------------------------------------------
# Save detection results
# ---------------------------------------------

with open("detected_data.json", "w", encoding="utf-8") as file:
    json.dump(detected_data, file, indent=4)

print()
print(f"Total sensitive items: {len(detected_data)}")
print("📁 Detection results saved to: detected_data.json")
print("✅ Detection completed!")