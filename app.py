from flask import Flask, render_template, request, send_file, jsonify
import os
import shutil
import subprocess
import socket
from PyPDF2 import PdfMerger, PdfReader, PdfWriter
from datetime import datetime
import uuid


app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
FEEDBACK_FOLDER = "feedback"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(FEEDBACK_FOLDER, exist_ok=True)


def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    except:
        ip = "127.0.0.1"
    finally:
        s.close()
    return ip


@app.route("/")
def home():
    return render_template("index.html")


# ===================== COMPRESS =====================
@app.route("/compress", methods=["POST"])
def compress():
    file = request.files.get("pdf")
    if not file:
        return jsonify({"error": "No PDF file uploaded."}), 400

    size_str = (request.form.get("size") or "").strip()
    if not size_str:
        return jsonify({"error": "Please enter target size (KB)."}), 400

    try:
        target_mb = float(size_str)
        target_kb = target_mb * 1024
    except ValueError:
        return jsonify({"error": "Target size must be number."}), 400

    input_path = os.path.join(UPLOAD_FOLDER, file.filename)
    output_path = os.path.join(UPLOAD_FOLDER, "compressed_" + file.filename)

    file.save(input_path)

    # Absolute paths (important)
    input_path = os.path.abspath(input_path)
    output_path = os.path.abspath(output_path)

    # Ghostscript path (update if needed)
    gs_path = r"C:\Program Files\gs\gs10.07.0\bin\gswin64c.exe"

    levels = ["/ebook", "/screen"]

    before = os.path.getsize(input_path) / 1024
    best_size_kb = before
    best_temp_path = None
    aggressive_used = False

    # ---- Normal compression levels ----
    
    # for level in levels:
    #     temp_output = output_path + f".{level.lstrip('/')}"

    #     cmd = [
    #         gs_path,
    #         "-sDEVICE=pdfwrite",
    #         "-dCompatibilityLevel=1.4",
    #         f"-dPDFSETTINGS={level}",
    #         "-dNOPAUSE",
    #         "-dQUIET",
    #         "-dBATCH",
    #         f"-sOutputFile={temp_output}",
    #         input_path
    #     ]

    #     result = subprocess.run(cmd, capture_output=True, text=True)

    #     print("RETURN CODE:", result.returncode)
    #     print("STDOUT:", result.stdout)
    #     print("STDERR:", result.stderr)

    #     if not os.path.exists(temp_output):
    #         continue

    #     size_kb = os.path.getsize(temp_output) / 1024

    #     if size_kb < best_size_kb:
    #         best_size_kb = size_kb
    #         best_temp_path = temp_output

    #     if size_kb <= target_kb:
    #         break

    # ---- Aggressive compression ----
    used_dpi = "N/A"
    if best_size_kb > target_kb:
        aggressive_used = True
        for res in [150, 125, 100 ,90,80,70,60, 50, 25]:
            temp_output = output_path + f".res{res}"

            cmd = [
                gs_path,
                "-sDEVICE=pdfwrite",
                "-dCompatibilityLevel=1.4",
                "-dPDFSETTINGS=/screen",
                "-dNOPAUSE",
                "-dQUIET",
                "-dBATCH",
                "-dDownsampleColorImages=true",
                "-dDownsampleGrayImages=true",
                "-dDownsampleMonoImages=true",
                f"-dColorImageResolution={res}",
                f"-dGrayImageResolution={res}",
                f"-dMonoImageResolution={res}",
                f"-sOutputFile={temp_output}",
                input_path
            ]

            subprocess.run(cmd)

            if not os.path.exists(temp_output):
                continue

            size_kb = os.path.getsize(temp_output) / 1024

            if size_kb < best_size_kb:
                best_size_kb = size_kb
                best_temp_path = temp_output
                used_dpi = f"{res} DPI"

            if size_kb <= target_kb:
                break

    # ---- Final output ----
    if best_temp_path and best_size_kb < before:
        shutil.copyfile(best_temp_path, output_path)
    else:
        shutil.copyfile(input_path, output_path)
        best_size_kb = before

    after = best_size_kb
    compressed = after < before

    message = (
        f"Compressed to {round(after/1024,2)} MB (target {target_mb} MB)."
        if compressed else
        "No further compression possible."
    )

    return jsonify({
        "download": "/download/" + os.path.basename(output_path),
        "before": round(before / 1024, 2),
        "after": round(after / 1024, 2),
        "compressed": compressed,
        "aggressive": aggressive_used,
        "dpi": used_dpi, 
        "message": message
    })


# ===================== DOWNLOAD =====================
@app.route("/download/<filename>")
def download(filename):
    path = os.path.join(UPLOAD_FOLDER, filename)
    return send_file(path, as_attachment=True)


# ===================== MERGE =====================
@app.route("/merge", methods=["POST"])
def merge():
    files = request.files.getlist("pdfs")
    merger = PdfMerger()

    for file in files:
        merger.append(file)

    output = os.path.join(UPLOAD_FOLDER, "merged.pdf")
    merger.write(output)
    merger.close()

    return send_file(output, as_attachment=True)


# ===================== SPLIT =====================
@app.route("/split", methods=["POST"])
def split():
    file = request.files["pdf"]

    reader = PdfReader(file)
    writer = PdfWriter()

    writer.add_page(reader.pages[0])

    output = os.path.join(UPLOAD_FOLDER, "page1.pdf")

    with open(output, "wb") as f:
        writer.write(f)

    return send_file(output, as_attachment=True)
# ===================== FEEDBACK =====================
@app.route("/feedback", methods=["POST"])
def feedback():

    data = request.get_json()

    text = (data.get("feedback") or "").strip()

    if not text:
        return jsonify({"error": "Feedback cannot be empty."}), 400

    filepath = os.path.join(FEEDBACK_FOLDER, "feedback.txt")

    with open(filepath, "a", encoding="utf-8") as f:

        f.write("Date : " + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + "\n")
        f.write("IP   : " + request.remote_addr + "\n")
        f.write("Feedback : " + text + "\n")
        f.write("-" * 60 + "\n")

    return jsonify({"message": "success"})

# ===================== SERVER =====================
from waitress import serve

if __name__ == "__main__":
    ip = get_local_ip()

    print("\n=============================")
    print("   PDF TOOLKIT SERVER")
    print("=============================")
    print("Local : http://127.0.0.1:5000")
    print(f"LAN   : http://{ip}:5000")
    print("=============================\n")

    serve(app, host="0.0.0.0", port=5000, threads=16)
