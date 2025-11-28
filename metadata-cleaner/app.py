import os
import zipfile
from flask import Flask, render_template, request, send_file, redirect, url_for
from werkzeug.utils import secure_filename
from cleaner.image_cleaner import clean_image
from cleaner.pdf_cleaner import clean_pdf
from cleaner.docx_cleaner import clean_docx
from cleaner.metadata_analyzer import extract_metadata, infer_privacy_risks

# Config
UPLOAD_FOLDER = "uploads"
CLEANED_FOLDER = "cleaned"
ALLOWED_EXT = {"jpg", "jpeg", "png", "pdf", "docx"}

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["CLEANED_FOLDER"] = CLEANED_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 200 * 1024 * 1024  # 200 MB limit, adjust if needed

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(CLEANED_FOLDER, exist_ok=True)


def allowed_extension(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXT


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        if "file" not in request.files:
            return "No file part in request", 400

        files = request.files.getlist("file")
        if not files or files == [None]:
            return "No files selected", 400

        analyses = []  # list of dicts with filename, metadata, inference, cleaned_name
        cleaned_files = []

        for f in files:
            if f.filename == "":
                continue
            filename = secure_filename(f.filename)
            if not allowed_extension(filename):
                analyses.append({
                    "original": filename,
                    "error": "File type not supported"
                })
                continue

            save_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            f.save(save_path)

            ext = filename.rsplit(".", 1)[1].lower()

            # extract metadata & inference BEFORE cleaning
            metadata = extract_metadata(save_path, ext)
            inference = infer_privacy_risks(metadata)

            # prepare cleaned filename
            cleaned_name = f"cleaned_{filename}"
            cleaned_path = os.path.join(app.config["CLEANED_FOLDER"], cleaned_name)

            # Clean file by type
            try:
                if ext in ["jpg", "jpeg", "png"]:
                    clean_image(save_path, cleaned_path)
                elif ext == "pdf":
                    clean_pdf(save_path, cleaned_path)
                elif ext == "docx":
                    clean_docx(save_path, cleaned_path)
                else:
                    # unsupported (shouldn't happen due to check)
                    raise ValueError("Unsupported file type")
                cleaned_files.append(cleaned_path)
                analyses.append({
                    "original": filename,
                    "cleaned": cleaned_name,
                    "metadata": metadata,
                    "inference": inference
                })
            except Exception as e:
                analyses.append({
                    "original": filename,
                    "error": f"Cleaning failed: {str(e)}"
                })

        # If no successful cleaned files, show result page with errors only
        if not cleaned_files:
            return render_template("result.html", analyses=analyses, zip_ready=False)

        # Create a ZIP containing cleaned files
        zip_name = "cleaned_files.zip"
        zip_path = os.path.join(app.config["CLEANED_FOLDER"], zip_name)
        # Remove old zip if exists
        if os.path.exists(zip_path):
            os.remove(zip_path)

        with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            for p in cleaned_files:
                # write with arcname as basename so ZIP has clean filenames
                zf.write(p, arcname=os.path.basename(p))

        # Render result page with analyses and link to download the zip
        return render_template("result.html", analyses=analyses, zip_ready=True, zip_name=zip_name)

    return render_template("index.html")


@app.route("/download/<path:filename>")
def download(filename):
    path = os.path.join(app.config["CLEANED_FOLDER"], filename)
    if not os.path.exists(path):
        return "File not found", 404
    return send_file(path, as_attachment=True)


if __name__ == "__main__":
    app.run(debug=True)
