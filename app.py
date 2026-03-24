from flask import Flask, render_template, request, send_file, jsonify
import os
import shutil
import subprocess
import socket
from PyPDF2 import PdfMerger, PdfReader, PdfWriter

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8",80))
        ip = s.getsockname()[0]
    except:
        ip = "127.0.0.1"
    finally:
        s.close()
    return ip


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/compress", methods=["POST"])
def compress():

    file = request.files.get("pdf")
    if not file:
        return jsonify({"error": "No PDF file uploaded."}), 400

    size_str = (request.form.get("size") or "").strip()
    if not size_str:
        return jsonify({"error": "Please enter a target size in KB."}), 400

    try:
        target_kb = int(size_str)
    except ValueError:
        return jsonify({"error": "Target size must be a whole number (KB)."}), 400

    input_path = os.path.join(UPLOAD_FOLDER, file.filename)
    output_path = os.path.join(UPLOAD_FOLDER, "compressed_" + file.filename)

    file.save(input_path)

    gs_path = r"C:\Program Files\gs\gs10.06.0\bin\gswin64c.exe"

    levels = ["/ebook", "/screen"]

    # Keep track of the best (smallest) output file we can produce
    before = os.path.getsize(input_path) / 1024
    best_size_kb = before
    best_temp_path = None
    aggressive_used = False

    for level in levels:
        temp_output = output_path + f".{level.lstrip('/')}"

        cmd = [
            gs_path,
            "-sDEVICE=pdfwrite",
            "-dCompatibilityLevel=1.4",
            f"-dPDFSETTINGS={level}",
            "-dNOPAUSE",
            "-dQUIET",
            "-dBATCH",
            f"-sOutputFile={temp_output}",
            input_path
        ]

        subprocess.run(cmd)

        size_kb = os.path.getsize(temp_output) / 1024

        # Save the smallest result
        if size_kb < best_size_kb:
            best_size_kb = size_kb
            best_temp_path = temp_output

        # Stop early if we've reached the target
        if size_kb <= target_kb:
            best_temp_path = temp_output
            best_size_kb = size_kb
            break

    # If we still didn't reach the requested target, try an aggressive image downsample pass.
    if best_size_kb > target_kb and target_kb < before:
        aggressive_used = True
        for res in [150, 100, 75, 50, 25]:
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

            size_kb = os.path.getsize(temp_output) / 1024

            if size_kb < best_size_kb:
                best_size_kb = size_kb
                best_temp_path = temp_output

            if size_kb <= target_kb:
                best_temp_path = temp_output
                best_size_kb = size_kb
                break

    # If we didn't get a smaller file, keep the original
    if best_temp_path and best_size_kb < before:
        shutil.copyfile(best_temp_path, output_path)
    else:
        shutil.copyfile(input_path, output_path)
        best_size_kb = before

    after = best_size_kb
    compressed = after < before

    # Build a clearer message depending on whether we forced an aggressive attempt.
    if compressed:
        message = f"Compressed to {round(after,2)} KB (target {target_kb} KB)."
        if aggressive_used:
            message = "Aggressive compression applied. " + message
    else:
        message = "No further compression was possible; returning original file."

    return jsonify({
        "download": "/download/" + os.path.basename(output_path),
        "before": round(before, 2),
        "after": round(after, 2),
        "compressed": compressed,
        "aggressive": aggressive_used,
        "message": message
    })


@app.route("/download/<filename>")
def download(filename):

    path = os.path.join(UPLOAD_FOLDER,filename)

    return send_file(path,as_attachment=True)


@app.route("/merge",methods=["POST"])
def merge():

    files = request.files.getlist("pdfs")

    merger = PdfMerger()

    for file in files:
        merger.append(file)

    output = os.path.join(UPLOAD_FOLDER,"merged.pdf")

    merger.write(output)
    merger.close()

    return send_file(output,as_attachment=True)


@app.route("/split",methods=["POST"])
def split():

    file = request.files["pdf"]

    reader = PdfReader(file)

    writer = PdfWriter()

    writer.add_page(reader.pages[0])

    output = os.path.join(UPLOAD_FOLDER,"page1.pdf")

    with open(output,"wb") as f:
        writer.write(f)

    return send_file(output,as_attachment=True)


from waitress import serve

if __name__ == "__main__":

    ip = get_local_ip()

    print("\n=============================")
    print("   PDF TOOLKIT SERVER")
    print("=============================")
    print("Local : http://127.0.0.1:5000")
    print(f"LAN   : http://{ip}:5000")
    print("=============================\n")

    serve(app, host="0.0.0.0", port=5000)