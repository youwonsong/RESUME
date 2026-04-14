from flask import Flask, send_from_directory, request, jsonify
import os
from add_data import build_context, Extractor
from docxtpl import DocxTemplate
import time
import traceback

app = Flask(
    __name__,
    static_folder="../Frontend",
    static_url_path=""
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_DIR = os.path.join(BASE_DIR, "spreadsheets")
OUTPUT_DIR = os.path.join(BASE_DIR, "outputs")

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

@app.route("/")
def index():
    return app.send_static_file("index.html")

@app.route("/upload", methods=["POST"])
def upload():
    file = request.files["file"]
    filepath = os.path.join(UPLOAD_DIR, file.filename)
    file.save(filepath)
    return jsonify({"message": "File uploaded.", "filename": file.filename})

@app.route("/generate", methods=["POST"])
def generate():
    data = request.get_json()
    filename = data.get("filename")
    template_name = data.get("template")

    if not filename:
        return jsonify({"error": "No filename provided."}), 400
    if not template_name:
        return jsonify({"error": "No template selected."}), 400

    spreadsheet_path = os.path.join(UPLOAD_DIR, filename)

    template_path = os.path.join(BASE_DIR, "templates", template_name)

    output_filename = f"output_{int(time.time())}.docx"
    output_path = os.path.join(OUTPUT_DIR, output_filename)

    try:
        extract = Extractor(spreadsheet_path)

        def normalize(method):
            def wrapper():
                result = method()

                if isinstance(result, tuple):
                    if len(result) == 2 and hasattr(result[1], "iloc"):
                        return result

                    years = None
                    dataframe = None

                    for item in result:
                        if isinstance(item, int) and years is None:
                            years = item
                        elif hasattr(item, "iloc") and dataframe is None:
                            dataframe = item

                    if dataframe is not None:
                        return (years, dataframe)

                if hasattr(result, "iloc"):
                    return (None, result)

                return result
            return wrapper

        extract.grab_key_personnel = normalize(extract.grab_key_personnel)
        extract.grab_other_personnel = normalize(extract.grab_other_personnel)
        extract.grab_benefits = normalize(extract.grab_benefits)
        extract.grab_direct_cost = normalize(extract.grab_direct_cost)
        extract.grab_domestic_travel = normalize(extract.grab_domestic_travel)
        
        context = build_context(extract)

        doc = DocxTemplate(template_path)
        doc.render(context)
        doc.save(output_path)

        return jsonify({"message": "Document generated.", "generatedName": output_filename})
    except Exception as e:
        print("ERROR in /generate:", e)
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route("/documents", methods=["GET"])
def list_documents():
    documents = []

    for filename in os.listdir(OUTPUT_DIR):
        if filename.lower().endswith(".docx"):
            filepath = os.path.join(OUTPUT_DIR, filename)
            documents.append({
                "name": filename,
                "generatedName": filename,
                "date": os.path.getmtime(filepath)
            })
    documents.sort(key=lambda doc: doc["date"], reverse=True)
    return jsonify(documents)

@app.route("/download/<filename>")
def download(filename):
    return send_from_directory(OUTPUT_DIR, filename, as_attachment=True)

@app.route("/delete/<filename>", methods=["DELETE"])
def delete_document(filename):
    filepath = os.path.join(OUTPUT_DIR, filename)

    if not os.path.exists(filepath):
        return jsonify({"error": "File not found."}), 404

    try:
        os.remove(filepath)
        return jsonify({"message": "File deleted."})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)