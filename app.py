from flask import (
    Flask,
    request,
    jsonify,
    send_file,
    send_from_directory
)

from flask_cors import CORS

from PIL import Image

import os
import subprocess
import sys
import json
import shutil
import time


# ============================================================
# DOCSHIELD - FINAL FLASK APPLICATION
# ============================================================

app = Flask(__name__)

CORS(app)


# ============================================================
# PATHS
# ============================================================

BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)


UPLOAD_FOLDER = os.path.join(
    BASE_DIR,
    "uploads"
)

FRONTEND_FOLDER = os.path.join(
    BASE_DIR,
    "frontend"
)

SAMPLE_FOLDER = os.path.join(
    BASE_DIR,
    "sample"
)


INPUT_FILE = os.path.join(
    UPLOAD_FOLDER,
    "input_document.jpg"
)

OUTPUT_FILE = os.path.join(
    SAMPLE_FOLDER,
    "protected_document.png"
)

DETECTED_FILE = os.path.join(
    BASE_DIR,
    "detected_data.json"
)


# ============================================================
# CREATE REQUIRED DIRECTORIES
# ============================================================

os.makedirs(
    UPLOAD_FOLDER,
    exist_ok=True
)

os.makedirs(
    SAMPLE_FOLDER,
    exist_ok=True
)


# ============================================================
# ALLOWED FILE TYPES
# ============================================================

ALLOWED_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".webp"
}


def allowed_file(filename):

    extension = os.path.splitext(
        filename
    )[1].lower()

    return extension in ALLOWED_EXTENSIONS


# ============================================================
# HOME
# ============================================================

@app.route("/")
def home():

    return jsonify({

        "status": "online",

        "application": "DocShield",

        "version": "SIH2026",

        "message":
            "DocShield AI Document Protection API is running"

    })


# ============================================================
# WEB UI
# ============================================================

@app.route("/ui")
def ui():

    return send_from_directory(
        FRONTEND_FOLDER,
        "index.html"
    )


# ============================================================
# PROTECTION API
# ============================================================

@app.route(
    "/protect",
    methods=["POST"]
)
def protect_document():

    # --------------------------------------------------------
    # CHECK FILE
    # --------------------------------------------------------

    if "file" not in request.files:

        return jsonify({

            "success": False,

            "error":
                "No file uploaded"

        }), 400


    uploaded_file = request.files["file"]


    if uploaded_file.filename == "":

        return jsonify({

            "success": False,

            "error":
                "No file selected"

        }), 400


    # --------------------------------------------------------
    # CHECK EXTENSION
    # --------------------------------------------------------

    if not allowed_file(
        uploaded_file.filename
    ):

        return jsonify({

            "success": False,

            "error":
                "Unsupported file type. Please upload JPG, JPEG, PNG or WEBP."

        }), 400


    # --------------------------------------------------------
    # SAVE IMAGE
    # --------------------------------------------------------

    try:

        image = Image.open(
            uploaded_file
        )

        image = image.convert(
            "RGB"
        )


        image.save(
            INPUT_FILE,
            "JPEG",
            quality=95
        )


        print()
        print("=" * 60)
        print(
            "DOCSHIELD - NEW DOCUMENT RECEIVED"
        )
        print("=" * 60)

        print(
            "Original file:",
            uploaded_file.filename
        )

        print(
            "Saved as:",
            INPUT_FILE
        )


    except Exception as error:

        print(
            "Upload processing error:",
            error
        )

        return jsonify({

            "success": False,

            "error":
                "Could not process uploaded image",

            "details":
                str(error)

        }), 500


    # --------------------------------------------------------
    # REMOVE OLD OUTPUT
    # --------------------------------------------------------

    for old_file in [
        OUTPUT_FILE,
        DETECTED_FILE
    ]:

        if os.path.exists(
            old_file
        ):

            try:

                os.remove(
                    old_file
                )

            except Exception as error:

                print(
                    "Could not remove old file:",
                    error
                )


    # --------------------------------------------------------
    # PIPELINE
    # --------------------------------------------------------

    scripts = [

        "preprocess.py",

        "perspective.py",

        "ocr.py",

        "detector.py",

        "visual_redactor.py"

    ]


    # --------------------------------------------------------
    # UTF-8 ENVIRONMENT
    # --------------------------------------------------------

    env = os.environ.copy()

    env[
        "PYTHONIOENCODING"
    ] = "utf-8"


    # --------------------------------------------------------
    # RUN PIPELINE
    # --------------------------------------------------------

    pipeline_results = []


    for script in scripts:

        print()
        print("=" * 60)

        print(
            "RUNNING:",
            script
        )

        print("=" * 60)


        script_path = os.path.join(
            BASE_DIR,
            script
        )


        if not os.path.exists(
            script_path
        ):

            return jsonify({

                "success": False,

                "error":
                    f"{script} not found"

            }), 500


        try:

            result = subprocess.run(

                [
                    sys.executable,
                    script_path
                ],

                capture_output=True,

                text=True,

                encoding="utf-8",

                errors="replace",

                env=env,

                cwd=BASE_DIR

            )


        except Exception as error:

            print(
                "Could not start:",
                script
            )

            print(
                error
            )


            return jsonify({

                "success": False,

                "error":
                    f"Could not start {script}",

                "details":
                    str(error)

            }), 500


        # ----------------------------------------------------
        # PRINT OUTPUT
        # ----------------------------------------------------

        if result.stdout:

            print(
                result.stdout
            )


        if result.stderr:

            print(
                result.stderr
            )


        # ----------------------------------------------------
        # FAILED SCRIPT
        # ----------------------------------------------------

        if result.returncode != 0:

            error_text = (
                result.stderr
                or
                result.stdout
                or
                "Unknown error"
            )


            print()
            print("=" * 60)

            print(
                "PIPELINE FAILED:",
                script
            )

            print("=" * 60)


            return jsonify({

                "success": False,

                "error":
                    f"{script} failed",

                "details":
                    error_text

            }), 500


        pipeline_results.append(
            script
        )


    # ========================================================
    # VERIFY OUTPUT
    # ========================================================

    if not os.path.exists(
        OUTPUT_FILE
    ):

        return jsonify({

            "success": False,

            "error":
                "Protected document was not generated"

        }), 500


    # ========================================================
    # READ DETECTIONS
    # ========================================================

    detected_data = []

    detection_types = {}


    if os.path.exists(
        DETECTED_FILE
    ):

        try:

            with open(
                DETECTED_FILE,
                "r",
                encoding="utf-8"
            ) as file:

                detected_data = json.load(
                    file
                )


        except Exception as error:

            print(
                "Could not read detection results:"
            )

            print(
                error
            )


    # --------------------------------------------------------
    # NORMALIZE DETECTIONS
    # --------------------------------------------------------

    if not isinstance(
        detected_data,
        list
    ):

        detected_data = []


    # --------------------------------------------------------
    # COUNT TYPES
    # --------------------------------------------------------

    for item in detected_data:

        data_type = item.get(
            "type",
            "Unknown"
        )


        detection_types[
            data_type
        ] = (
            detection_types.get(
                data_type,
                0
            )
            + 1
        )


    detected_count = len(
        detected_data
    )


    # ========================================================
    # PROTECTION COVERAGE
    # ========================================================

    if detected_count > 0:

        protection_status = (
            "Document protected successfully"
        )

        protection_state = "protected"

    else:

        protection_status = (
            "No sensitive information detected"
        )

        protection_state = "clean"


    # ========================================================
    # FINAL LOG
    # ========================================================

    print()
    print("=" * 60)

    print(
        "DOCSHIELD PROTECTION COMPLETED"
    )

    print("=" * 60)

    print(
        "Detected items:",
        detected_count
    )

    print(
        "Detection types:",
        detection_types
    )

    print(
        "Protected file:",
        OUTPUT_FILE
    )

    print(
        "=" * 60
    )


    # ========================================================
    # RESPONSE
    # ========================================================

    return jsonify({

        "success": True,

        "message":
            "Document protected successfully",

        "status":
            protection_state,

        "protection_message":
            protection_status,

        "detected_items":
            detected_count,

        "detection_types":
            detection_types,

        "pipeline":
            pipeline_results,

        "download":
            "/download",

        "preview":
            "/preview"

    })


# ============================================================
# PREVIEW
# ============================================================

@app.route(
    "/preview"
)
def preview_document():

    if not os.path.exists(
        OUTPUT_FILE
    ):

        return jsonify({

            "error":
                "Protected document not found"

        }), 404


    return send_file(

        OUTPUT_FILE,

        mimetype="image/png"

    )


# ============================================================
# DOWNLOAD
# ============================================================

@app.route(
    "/download"
)
def download_document():

    if not os.path.exists(
        OUTPUT_FILE
    ):

        return jsonify({

            "error":
                "Protected document not found"

        }), 404


    return send_file(

        OUTPUT_FILE,

        as_attachment=True,

        download_name=
            "DocShield_Protected.png"

    )


# ============================================================
# ERROR HANDLER
# ============================================================

@app.errorhandler(
    413
)
def file_too_large(error):

    return jsonify({

        "success": False,

        "error":
            "Uploaded file is too large"

    }), 413


# ============================================================
# START SERVER
# ============================================================

if __name__ == "__main__":

    print()
    print("=" * 60)

    print(
        "           DOCSHIELD AI DOCUMENT PROTECTION"
    )

    print("=" * 60)

    print()

    print(
        "API:"
    )

    print(
        "http://127.0.0.1:5000"
    )

    print()

    print(
        "Web Interface:"
    )

    print(
        "http://127.0.0.1:5000/ui"
    )

    print()

    print(
        "Upload endpoint:"
    )

    print(
        "http://127.0.0.1:5000/protect"
    )

    print()

    print("=" * 60)

    print()


    app.run(

        host="127.0.0.1",

        port=5000,

        debug=True

    )