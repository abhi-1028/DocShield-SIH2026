import json
import re


# --------------------------------------------------
# Load OCR results
# --------------------------------------------------

with open("ocr_results.json", "r", encoding="utf-8") as file:
    ocr_data = json.load(file)


print("🔍 Scanning OCR results for sensitive information...")
print()


# --------------------------------------------------
# Store detected sensitive information
# --------------------------------------------------

detected_data = []


# --------------------------------------------------
# Check every OCR text line
# --------------------------------------------------

for item in ocr_data:

    text = item["text"]
    box = item["box"]


    # ---------------------------------------------
    # 1. Detect Name
    # ---------------------------------------------

    name_match = re.search(
        r"\b(?:Name|Full Name)\s*:\s*(.+)",
        text,
        re.IGNORECASE
    )

    if name_match:

        name = name_match.group(1).strip()

        detected_data.append({
            "type": "NAME",
            "value": name,
            "box": box
        })


    # ---------------------------------------------
    # 2. Detect ID
    # ---------------------------------------------

    id_match = re.search(
        r"\b(?:ID|ID Number|Document ID)\s*:\s*([A-Za-z0-9-]+)",
        text,
        re.IGNORECASE
    )

    if id_match:

        document_id = id_match.group(1).strip()

        detected_data.append({
            "type": "ID",
            "value": document_id,
            "box": box
        })


    # ---------------------------------------------
    # 3. Detect Date of Birth
    # ---------------------------------------------

    dob_match = re.search(
        r"\b(?:DOB|Date of Birth|Birth Date)\s*:\s*"
        r"(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})",
        text,
        re.IGNORECASE
    )

    if dob_match:

        dob = dob_match.group(1).strip()

        detected_data.append({
            "type": "DATE OF BIRTH",
            "value": dob,
            "box": box
        })


    # ---------------------------------------------
    # 4. Detect Indian Phone Number
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
            "box": box
        })


    # ---------------------------------------------
    # 5. Detect Email Address
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
            "box": box
        })


    # ---------------------------------------------
    # 6. Detect Aadhaar-style Number
    # ---------------------------------------------

    aadhaar_match = re.search(
        r"\b\d{4}[\s-]\d{4}[\s-]\d{4}\b",
        text
    )

    if aadhaar_match:

        aadhaar = aadhaar_match.group(0).strip()

        detected_data.append({
            "type": "AADHAAR NUMBER",
            "value": aadhaar,
            "box": box
        })


# --------------------------------------------------
# Display Results
# --------------------------------------------------

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


# --------------------------------------------------
# Save Detection Results
# --------------------------------------------------

with open(
    "detected_data.json",
    "w",
    encoding="utf-8"
) as file:

    json.dump(
        detected_data,
        file,
        indent=4
    )


print()
print(f"Total sensitive items: {len(detected_data)}")
print("📁 Detection results saved to: detected_data.json")
print("✅ Detection completed!")