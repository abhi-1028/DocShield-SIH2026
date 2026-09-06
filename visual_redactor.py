import cv2
import json


# ============================================================
# DOCSHIELD - FINAL VISUAL REDACTION ENGINE
# ============================================================

INPUT_IMAGE = "sample/straight_document.png"
DETECTED_DATA_FILE = "detected_data.json"
OUTPUT_IMAGE = "sample/protected_document.png"

# Safety margin around OCR detection boxes
PADDING_X = 28
PADDING_Y = 18


# ============================================================
# LOAD IMAGE
# ============================================================

image = cv2.imread(
    INPUT_IMAGE
)

if image is None:

    print(
        "ERROR: Could not load corrected document image!"
    )

    print(
        "Expected:",
        INPUT_IMAGE
    )

    exit(1)


# ============================================================
# LOAD DETECTION RESULTS
# ============================================================

try:

    with open(
        DETECTED_DATA_FILE,
        "r",
        encoding="utf-8"
    ) as file:

        detected_data = json.load(file)

except Exception as error:

    print(
        "ERROR: Could not load detected data!"
    )

    print(error)

    exit(1)


if not isinstance(
    detected_data,
    list
):

    print(
        "ERROR: Detection data must be a list!"
    )

    exit(1)


print(
    "Protecting detected sensitive information..."
)

print()


# ============================================================
# IMAGE SIZE
# ============================================================

image_height, image_width = image.shape[:2]


# ============================================================
# CREATE VALID REDACTION BOXES
# ============================================================

redaction_boxes = []


for item in detected_data:

    text_type = item.get(
        "type",
        "Unknown"
    )

    box = item.get(
        "box",
        []
    )


    # --------------------------------------------------------
    # VALIDATE BOX
    # --------------------------------------------------------

    if not isinstance(
        box,
        list
    ) or len(box) != 4:

        print(
            f"Skipped {text_type}: invalid bounding box"
        )

        continue


    try:

        x1, y1, x2, y2 = [
            int(float(value))
            for value in box
        ]

    except Exception:

        print(
            f"Skipped {text_type}: invalid coordinates"
        )

        continue


    # --------------------------------------------------------
    # NORMALIZE COORDINATES
    # --------------------------------------------------------

    if x1 > x2:

        x1, x2 = x2, x1

    if y1 > y2:

        y1, y2 = y2, y1


    # --------------------------------------------------------
    # ADD SAFETY PADDING
    # --------------------------------------------------------

    x1 -= PADDING_X
    y1 -= PADDING_Y
    x2 += PADDING_X
    y2 += PADDING_Y


    # --------------------------------------------------------
    # CLIP TO IMAGE
    # --------------------------------------------------------

    x1 = max(
        0,
        min(
            x1,
            image_width - 1
        )
    )

    y1 = max(
        0,
        min(
            y1,
            image_height - 1
        )
    )

    x2 = max(
        0,
        min(
            x2,
            image_width - 1
        )
    )

    y2 = max(
        0,
        min(
            y2,
            image_height - 1
        )
    )


    # --------------------------------------------------------
    # VALIDATE
    # --------------------------------------------------------

    if x2 <= x1 or y2 <= y1:

        print(
            f"Skipped {text_type}: invalid final box"
        )

        continue


    redaction_boxes.append(
        (
            x1,
            y1,
            x2,
            y2,
            text_type
        )
    )


# ============================================================
# MERGE OVERLAPPING BOXES
# ============================================================

def boxes_overlap(
    box_a,
    box_b
):

    ax1, ay1, ax2, ay2 = box_a[:4]
    bx1, by1, bx2, by2 = box_b[:4]


    return not (
        ax2 < bx1
        or
        bx2 < ax1
        or
        ay2 < by1
        or
        by2 < ay1
    )


merged_boxes = []


for box in redaction_boxes:

    merged = False

    for index in range(
        len(merged_boxes)
    ):

        existing = merged_boxes[index]

        if boxes_overlap(
            existing,
            box
        ):

            x1 = min(
                existing[0],
                box[0]
            )

            y1 = min(
                existing[1],
                box[1]
            )

            x2 = max(
                existing[2],
                box[2]
            )

            y2 = max(
                existing[3],
                box[3]
            )

            types = (
                existing[4]
                + ", "
                + box[4]
            )

            merged_boxes[index] = (
                x1,
                y1,
                x2,
                y2,
                types
            )

            merged = True

            break


    if not merged:

        merged_boxes.append(
            box
        )


# ============================================================
# REDACT
# ============================================================

protected_count = 0


for box in merged_boxes:

    x1, y1, x2, y2, text_type = box


    cv2.rectangle(
        image,
        (x1, y1),
        (x2, y2),
        (0, 0, 0),
        -1
    )


    protected_count += 1


    print(
        f"Protected: {text_type}"
    )

    print(
        f"Protected box: [{x1}, {y1}, {x2}, {y2}]"
    )

    print()


# ============================================================
# SAVE PROTECTED DOCUMENT
# ============================================================

success = cv2.imwrite(
    OUTPUT_IMAGE,
    image
)


if not success:

    print(
        "ERROR: Could not save protected document!"
    )

    exit(1)


print(
    f"Total protected areas: {protected_count}"
)

print(
    f"Protected document saved to: {OUTPUT_IMAGE}"
)

print(
    "Visual redaction completed!"
)