# QR Code Generator

A self-hosted batch QR code generator built with Flask. Paste URLs or upload a `.txt` file to generate multiple QR codes at once, then download them individually or as a ZIP.

![Python](https://img.shields.io/badge/Python-3.9%2B-blue)
![Flask](https://img.shields.io/badge/Flask-3.0%2B-green)
![License](https://img.shields.io/badge/License-MIT-yellow)

## Features

- **Batch generation** — generate up to 20 QR codes at once
- **PNG & SVG output** — raster or vector format
- **Custom colors** — pick any foreground/background color
- **Error correction** — four levels (L / M / Q / H)
- **Adjustable size** — 100–2000px for PNG output
- **File upload** — drag-and-drop a `.txt` file of URLs
- **ZIP download** — download all generated codes in one click
- **Dark / Light theme** — toggles automatically based on system preference
- **Server-side validation** — file type, size, and content checks

## Quick Start

```bash
git clone https://github.com/nextframedev/qr-code-generator.git
cd qr-code-generator
bash start.sh
```

The app will:
1. Create a Python virtual environment
2. Install dependencies
3. Start the server at **http://localhost:5050**

## Manual Setup

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python3 app.py
```

## Usage

1. Open **http://localhost:5050** in your browser
2. **Enter URLs** — paste one URL per line, or upload a `.txt` file
3. **Configure options** (optional):
   - **Format** — PNG (raster) or SVG (vector)
   - **Error correction** — L (7%), M (15%), Q (25%), H (30%)
   - **Size** — pixel dimensions for PNG (ignored for SVG)
   - **Colors** — foreground and background hex colors
4. Click **Generate QR Codes**
5. **Download** individually or as a ZIP archive

### URL File Format

Plain text, one URL per line. Lines starting with `#` are treated as comments.

```text
# Example links
https://quietlinepress.com
https://nextframe.dev
https://opennote.dev
https://opennotes.dev
```

## Configuration

| Setting | Default | Range / Options |
|---------|---------|-----------------|
| Port | `5050` | Set in `app.py` |
| Debug mode | `true` | `FLASK_DEBUG` env var |
| Secret key | `qr-dev-secret` | `SECRET_KEY` env var |
| Max URLs per batch | 20 | — |
| PNG size | 300px | 100–2000px |
| Error correction | M | L / M / Q / H |
| Max upload file size | 1 MB | — |

## Project Structure

```
├── app.py              # Flask application
├── start.sh            # Startup script (venv + install + run)
├── requirements.txt    # Python dependencies
├── templates/
│   └── index.html      # Main page template
├── static/
│   └── css/
│       └── style.css   # Stylesheet (light/dark themes)
└── qrcodes/            # Generated QR codes (created at runtime)
```

## Requirements

- Python 3.9+
- Dependencies (installed automatically via `start.sh`):
  - Flask >= 3.0.0
  - Werkzeug >= 3.0.0
  - qrcode[pil] >= 7.4.0
  - Pillow >= 10.0.0

## License

MIT

## Books by the Authors

<p align="center">
  <a href="https://www.amazon.com/dp/B0GRVLNV2H">
    <img src="assets/books-qr.png" alt="QR code to our books on Amazon" width="200">
  </a>
  <br>
  <em>Scan to check out our books on Amazon</em>
</p>
