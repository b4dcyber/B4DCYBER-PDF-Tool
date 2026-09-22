# B4DCYBER PDF Tool — Web Version

## Features
- PDF preview with page thumbnails
- Merge multiple PDFs
- Reorder merge queue
- Extract pages
- Delete pages
- Rotate selected pages or all pages
- PDF to Word
- Image/scanned PDF to text (OCR)
- Dark B4DCYBER UI

## Windows setup

Install Python packages:

    python -m pip install -r requirements.txt

Run:

    python app.py

Open:

    http://127.0.0.1:5000

## OCR requirement

The OCR feature uses Tesseract OCR through pytesseract.

You must install the Tesseract OCR engine separately on Windows. If Tesseract is installed but not in PATH, set its path in app.py, for example:

    pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

OCR is intended for scanned/image-based PDFs. The output is a TXT file.

For better Urdu OCR, install an Urdu Tesseract language data file (urd.traineddata) and use:
    pytesseract.image_to_string(img, lang="urd+eng")

The current UI defaults to Tesseract's default English OCR.
