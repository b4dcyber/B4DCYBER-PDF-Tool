from flask import Flask, render_template, request, send_file, jsonify
from pypdf import PdfReader, PdfWriter
from docx import Document
import fitz
import os
import tempfile
import uuid
import io
import pytesseract

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"


app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 100 * 1024 * 1024  # 100 MB total request

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
WORK_DIR = os.path.join(BASE_DIR, "work")
os.makedirs(WORK_DIR, exist_ok=True)


def safe_name(name):
    return os.path.basename(name).replace("\x00", "")


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/preview", methods=["POST"])
def preview():
    if "file" not in request.files:
        return jsonify(error="No PDF uploaded."), 400

    file = request.files["file"]
    if not file.filename.lower().endswith(".pdf"):
        return jsonify(error="Please select a PDF file."), 400

    data = file.read()
    try:
        doc = fitz.open(stream=data, filetype="pdf")
        pages = []
        for i in range(len(doc)):
            page = doc.load_page(i)
            pix = page.get_pixmap(matrix=fitz.Matrix(0.8, 0.8), alpha=False)
            pages.append({
                "page": i + 1,
                "width": pix.width,
                "height": pix.height
            })
        return jsonify(filename=safe_name(file.filename), pages=pages)
    except Exception as e:
        return jsonify(error=str(e)), 500


@app.route("/preview-page", methods=["POST"])
def preview_page():
    if "file" not in request.files:
        return jsonify(error="No PDF uploaded."), 400
    file = request.files["file"]
    page_no = int(request.form.get("page", "1")) - 1
    data = file.read()
    try:
        doc = fitz.open(stream=data, filetype="pdf")
        if page_no < 0 or page_no >= len(doc):
            return jsonify(error="Invalid page number."), 400
        page = doc.load_page(page_no)
        pix = page.get_pixmap(matrix=fitz.Matrix(1.25, 1.25), alpha=False)
        out = io.BytesIO(pix.tobytes("png"))
        out.seek(0)
        return send_file(out, mimetype="image/png")
    except Exception as e:
        return jsonify(error=str(e)), 500


@app.route("/merge", methods=["POST"])
def merge():
    files = request.files.getlist("files")
    files = [f for f in files if f and f.filename]
    if len(files) < 2:
        return jsonify(error="Select at least two PDF files."), 400

    writer = PdfWriter()
    try:
        for f in files:
            reader = PdfReader(f.stream)
            for page in reader.pages:
                writer.add_page(page)

        output = os.path.join(WORK_DIR, f"merged_{uuid.uuid4().hex}.pdf")
        with open(output, "wb") as out:
            writer.write(out)

        return send_file(output, as_attachment=True,
                         download_name="B4DCYBER_Merged.pdf",
                         mimetype="application/pdf")
    except Exception as e:
        return jsonify(error=str(e)), 500


@app.route("/extract", methods=["POST"])
def extract():
    file = request.files.get("file")
    pages_text = request.form.get("pages", "").strip()
    if not file or not file.filename:
        return jsonify(error="No PDF uploaded."), 400
    if not pages_text:
        return jsonify(error="Enter pages, e.g. 1-3 or 1,3,5."), 400

    try:
        reader = PdfReader(file.stream)
        total = len(reader.pages)
        selected = parse_pages(pages_text, total)

        writer = PdfWriter()
        for idx in selected:
            writer.add_page(reader.pages[idx])

        output = os.path.join(WORK_DIR, f"extract_{uuid.uuid4().hex}.pdf")
        with open(output, "wb") as out:
            writer.write(out)

        return send_file(output, as_attachment=True,
                         download_name="B4DCYBER_Extracted.pdf",
                         mimetype="application/pdf")
    except Exception as e:
        return jsonify(error=str(e)), 400


def parse_pages(value, total):
    result = set()
    for part in value.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            bits = part.split("-")
            if len(bits) != 2:
                raise ValueError("Invalid page range.")
            start, end = int(bits[0]), int(bits[1])
            if start > end:
                start, end = end, start
            for p in range(start, end + 1):
                if 1 <= p <= total:
                    result.add(p - 1)
        else:
            p = int(part)
            if 1 <= p <= total:
                result.add(p - 1)

    if not result:
        raise ValueError(f"Invalid page selection. PDF has {total} page(s).")
    return sorted(result)


@app.route("/delete", methods=["POST"])
def delete():
    file = request.files.get("file")
    pages_text = request.form.get("pages", "").strip()
    if not file or not file.filename:
        return jsonify(error="No PDF uploaded."), 400
    if not pages_text:
        return jsonify(error="Enter pages to delete, e.g. 2 or 2,4-6."), 400

    try:
        reader = PdfReader(file.stream)
        total = len(reader.pages)
        remove = set(parse_pages(pages_text, total))

        if len(remove) >= total:
            return jsonify(error="You cannot delete all pages from a PDF."), 400

        writer = PdfWriter()
        for idx, page in enumerate(reader.pages):
            if idx not in remove:
                writer.add_page(page)

        output = os.path.join(WORK_DIR, f"delete_{uuid.uuid4().hex}.pdf")
        with open(output, "wb") as out:
            writer.write(out)

        return send_file(output, as_attachment=True,
                         download_name="B4DCYBER_DeletedPages.pdf",
                         mimetype="application/pdf")
    except Exception as e:
        return jsonify(error=str(e)), 400


@app.route("/rotate", methods=["POST"])
def rotate():
    file = request.files.get("file")
    pages_text = request.form.get("pages", "").strip()
    angle = int(request.form.get("angle", "90"))

    if not file or not file.filename:
        return jsonify(error="No PDF uploaded."), 400
    if angle not in (90, 180, 270):
        return jsonify(error="Angle must be 90, 180 or 270."), 400

    try:
        reader = PdfReader(file.stream)
        total = len(reader.pages)
        selected = set(parse_pages(pages_text, total)) if pages_text else set(range(total))

        writer = PdfWriter()
        for idx, page in enumerate(reader.pages):
            if idx in selected:
                page.rotate(angle)
            writer.add_page(page)

        output = os.path.join(WORK_DIR, f"rotate_{uuid.uuid4().hex}.pdf")
        with open(output, "wb") as out:
            writer.write(out)

        return send_file(output, as_attachment=True,
                         download_name="B4DCYBER_Rotated.pdf",
                         mimetype="application/pdf")
    except Exception as e:
        return jsonify(error=str(e)), 400


@app.route("/ocr", methods=["POST"])
def ocr():
    file = request.files.get("file")
    pages_text = request.form.get("pages", "").strip()

    if not file or not file.filename:
        return jsonify(error="No PDF uploaded."), 400

    try:
        data = file.read()
        pdf = fitz.open(stream=data, filetype="pdf")
        total = len(pdf)

        if pages_text:
            selected = parse_pages(pages_text, total)
        else:
            selected = list(range(total))

        text_parts = []
        for idx in selected:
            page = pdf.load_page(idx)
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
            from PIL import Image
            img = Image.open(io.BytesIO(pix.tobytes("png")))
            text = pytesseract.image_to_string(img)
            text_parts.append(f"--- Page {idx + 1} ---\n{text.strip()}")

        output = os.path.join(WORK_DIR, f"ocr_{uuid.uuid4().hex}.txt")
        with open(output, "w", encoding="utf-8") as out:
            out.write("\n\n".join(text_parts))

        return send_file(
            output,
            as_attachment=True,
            download_name="B4DCYBER_OCR_Text.txt",
            mimetype="text/plain; charset=utf-8"
        )
    except Exception as e:
        return jsonify(error=str(e)), 400


@app.route("/pdf-to-word", methods=["POST"])
def pdf_to_word():
    file = request.files.get("file")
    if not file or not file.filename:
        return jsonify(error="No PDF uploaded."), 400

    try:
        data = file.read()
        pdf = fitz.open(stream=data, filetype="pdf")
        document = Document()

        for page_no, page in enumerate(pdf):
            text = page.get_text("text")
            if text.strip():
                for line in text.splitlines():
                    document.add_paragraph(line)
            if page_no < len(pdf) - 1:
                document.add_page_break()

        output = os.path.join(WORK_DIR, f"word_{uuid.uuid4().hex}.docx")
        document.save(output)

        return send_file(output, as_attachment=True,
                         download_name="B4DCYBER_Converted.docx",
                         mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
    except Exception as e:
        return jsonify(error=str(e)), 400


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
