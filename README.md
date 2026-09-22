# B4DCYBER PDF Tool

Browser-based PDF utility by B4DCYBER.

## Features
- PDF preview and navigation
- Merge multiple PDFs
- Extract selected pages
- Delete selected pages
- Rotate the current page
- PDF to Word text extraction
- Image OCR
- OCR for the current PDF page
- Download processed files

## Privacy
Selected documents are processed in the browser; the application does not contain an application-server upload endpoint.

The initial page load fetches open-source JavaScript dependencies from configured CDNs. For fully offline or controlled environments, those dependencies can be self-hosted.

Review dependencies before using the tool with sensitive documents.

## Run
Open index.html, or serve the folder locally:

```bash
python -m http.server 8000
```

Then open http://localhost:8000.

## Notes
PDF-to-Word extracts text into DOCX and does not guarantee original layout preservation. Scanned PDFs can be processed with OCR.

No organization-specific or NRTC-specific information is included.
