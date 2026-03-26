#!/usr/bin/env python3
"""
Standalone QR Code Generator
Generates PNG/SVG QR codes from URLs — single or batch via text file.
"""

from flask import Flask, render_template, request, jsonify, send_file, send_from_directory
from werkzeug.utils import secure_filename
from pathlib import Path
import os
import io
import re
import base64
import uuid
import zipfile
import xml.etree.ElementTree as ET

# QR code library
try:
    import qrcode
    import qrcode.image.svg
    from PIL import Image as PILImage
    QR_SUPPORT = True
except ImportError:
    QR_SUPPORT = False

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'qr-dev-secret')

BASE_DIR = Path(__file__).parent
QR_FOLDER = BASE_DIR / 'qrcodes'
QR_FOLDER.mkdir(exist_ok=True)


# ---------------------------------------------------------------------------
# Pages
# ---------------------------------------------------------------------------

@app.route('/')
def index():
    return render_template('index.html', qr_support=QR_SUPPORT)


# ---------------------------------------------------------------------------
# API
# ---------------------------------------------------------------------------

@app.route('/generate_qrcode', methods=['POST'])
def generate_qrcode():
    """Generate QR codes from a list of URLs.

    Accepts:
      - urls        : textarea string, one URL per line
      - url_file    : optional .txt file upload (merged with textarea)
      - format      : 'png' (default) or 'svg'
      - size        : output pixel size for PNG (100–2000, default 300)
      - error_correction : L / M (default) / Q / H
      - fill_color  : hex foreground colour, default #000000
      - back_color  : hex background colour, default #ffffff

    Returns JSON:
      { session_id, results: [{url, filename, data (base64), format, error}] }
    """
    if not QR_SUPPORT:
        return jsonify({'error': 'qrcode library not installed — run: pip install "qrcode[pil]"'}), 500

    # ── Collect URLs ────────────────────────────────────────────────────────
    raw_text = request.form.get('urls', '')
    txt_file = request.files.get('url_file')
    if txt_file and txt_file.filename:
        filename = secure_filename(txt_file.filename)
        if not filename.lower().endswith('.txt'):
            return jsonify({'error': 'Only .txt files are allowed'}), 400
        # Reject files larger than 1 MB
        txt_file.seek(0, 2)
        if txt_file.tell() > 1_000_000:
            return jsonify({'error': 'File too large (max 1 MB)'}), 400
        txt_file.seek(0)
        try:
            content = txt_file.read()
            raw_text += '\n' + content.decode('utf-8')
        except (UnicodeDecodeError, Exception):
            return jsonify({'error': 'File does not appear to be a valid text file'}), 400

    urls = [line.strip() for line in raw_text.splitlines()
            if line.strip() and not line.strip().startswith('#')]

    if not urls:
        return jsonify({'error': 'No URLs provided'}), 400
    if len(urls) > 20:
        return jsonify({'error': 'Maximum 20 URLs per batch'}), 400

    # ── Settings ────────────────────────────────────────────────────────────
    fmt = request.form.get('format', 'png').lower()
    if fmt not in ('png', 'svg'):
        fmt = 'png'

    try:
        size = max(100, min(2000, int(request.form.get('size', 300))))
    except (ValueError, TypeError):
        size = 300

    ec_map = {
        'L': qrcode.constants.ERROR_CORRECT_L,
        'M': qrcode.constants.ERROR_CORRECT_M,
        'Q': qrcode.constants.ERROR_CORRECT_Q,
        'H': qrcode.constants.ERROR_CORRECT_H,
    }
    ec = ec_map.get(request.form.get('error_correction', 'M'), qrcode.constants.ERROR_CORRECT_M)

    hex_color_re = re.compile(r'^#[0-9a-fA-F]{6}$')
    fill_color = request.form.get('fill_color', '#000000')
    back_color = request.form.get('back_color', '#ffffff')
    if not hex_color_re.match(fill_color):
        fill_color = '#000000'
    if not hex_color_re.match(back_color):
        back_color = '#ffffff'

    # ── Output directory ────────────────────────────────────────────────────
    session_id = str(uuid.uuid4())
    out_dir = QR_FOLDER / session_id
    out_dir.mkdir(parents=True, exist_ok=True)

    SVG_NS = 'http://www.w3.org/2000/svg'
    ET.register_namespace('', SVG_NS)

    results = []
    for url in urls:
        try:
            qr = qrcode.QRCode(error_correction=ec, box_size=10, border=4)
            qr.add_data(url)
            qr.make(fit=True)

            safe_stem = re.sub(r'[^\w\-.]', '_', url)[:80].strip('_') or f'qr_{len(results) + 1}'

            if fmt == 'svg':
                img = qr.make_image(image_factory=qrcode.image.svg.SvgPathImage)
                buf = io.BytesIO()
                img.save(buf)
                raw_svg = buf.getvalue().decode('utf-8')

                # Inject custom colours via XML post-processing
                root = ET.fromstring(raw_svg)
                w = root.get('width', '100%')
                h = root.get('height', '100%')

                bg = ET.Element(f'{{{SVG_NS}}}rect')
                bg.set('width', w)
                bg.set('height', h)
                bg.set('fill', back_color)
                root.insert(0, bg)

                for el in root.iter(f'{{{SVG_NS}}}path'):
                    el.set('fill', fill_color)

                svg_final = ('<?xml version="1.0" encoding="UTF-8"?>\n' +
                             ET.tostring(root, encoding='unicode'))

                safe_name = safe_stem + '.svg'
                (out_dir / safe_name).write_text(svg_final, encoding='utf-8')
                b64 = base64.b64encode(svg_final.encode('utf-8')).decode()
                results.append({'url': url, 'filename': safe_name,
                                'data': b64, 'format': 'svg', 'error': None})

            else:  # PNG
                img = qr.make_image(fill_color=fill_color, back_color=back_color).convert('RGB')
                img = img.resize((size, size), PILImage.NEAREST)

                safe_name = safe_stem + '.png'
                img.save(out_dir / safe_name, format='PNG')

                buf = io.BytesIO()
                img.save(buf, format='PNG')
                buf.seek(0)
                b64 = base64.b64encode(buf.read()).decode()
                results.append({'url': url, 'filename': safe_name,
                                'data': b64, 'format': 'png', 'error': None})

        except Exception as e:
            results.append({'url': url, 'filename': None, 'data': None,
                            'format': fmt, 'error': str(e)})

    return jsonify({'session_id': session_id, 'results': results})


@app.route('/download_qrcodes/<session_id>')
def download_qrcodes(session_id):
    """Download all QR codes for a session as a ZIP."""
    try:
        uuid.UUID(session_id)
    except ValueError:
        return 'Invalid session', 400

    out_dir = QR_FOLDER / session_id
    if not out_dir.exists():
        return 'Session not found', 404

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf:
        for f in sorted(out_dir.iterdir()):
            if f.is_file():
                zf.write(f, f.name)
    buf.seek(0)
    return send_file(buf, mimetype='application/zip',
                     as_attachment=True, download_name='qrcodes.zip')


@app.route('/download_single_qr/<session_id>/<filename>')
def download_single_qr(session_id, filename):
    """Download a single QR code file."""
    try:
        uuid.UUID(session_id)
    except ValueError:
        return 'Invalid session', 400
    return send_from_directory(QR_FOLDER / session_id,
                               secure_filename(filename), as_attachment=True)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == '__main__':
    print('=' * 50)
    print('QR Code Generator')
    print('=' * 50)
    print(f'QR support: {"✓" if QR_SUPPORT else "✗  (pip install qrcode[pil])"}')
    print('Open: http://localhost:5050')
    print('=' * 50)
    debug = os.environ.get('FLASK_DEBUG', 'true').lower() == 'true'
    app.run(debug=debug, host='0.0.0.0', port=5050)
