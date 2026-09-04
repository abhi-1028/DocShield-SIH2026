import easyocr

_reader = None


def get_reader():
    global _reader

    if _reader is None:
        _reader = easyocr.Reader(["en"], gpu=False)

    return _reader


def extract_text(image_path: str) -> dict:
    reader = get_reader()

    results = reader.readtext(image_path)

    extracted_text = []
    detections = []

    for result in results:
        box, text, confidence = result

        extracted_text.append(text)

        detections.append({
            "text": text,
            "confidence": round(float(confidence), 4),
            "box": [[int(point[0]), int(point[1])] for point in box],
        })

    return {
        "text": "\n".join(extracted_text),
        "detections": detections,
        "text_count": len(extracted_text),
    }
