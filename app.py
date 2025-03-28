import os
from flask import Flask, render_template, request, redirect, url_for, flash
from werkzeug.utils import secure_filename
from analysis import FinancialAnalyzer 
import matplotlib.pyplot as plt
import pandas as pd
from io import BytesIO
import base64
import re

app = Flask(__name__)
app.secret_key = 'a3e2497fc9a13746c2694872d45e94216096e98f8d1369ff06914c4cdd04ab3d'  # Required for flash messages

UPLOAD_FOLDER = "uploads"
ALLOWED_EXTENSIONS = {"pdf"}
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB file size limit

# Initialize the analyzer
analyzer = FinancialAnalyzer(api_key='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')

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/upload", methods=["POST"])
def upload_file():
    if "file" not in request.files:
        flash("No file uploaded", "error")
        return redirect(url_for("index"))

    file = request.files["file"]
    company = request.form.get("company", "").strip()
    
    if file.filename == "":
        flash("No file selected", "error")
        return redirect(url_for("index"))

    if not company:
        flash("Company name is required", "error")
        return redirect(url_for("index"))

    if file and allowed_file(file.filename):
        try:
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            file.save(file_path)

            # Process the file
            report_text = analyzer.extract_text_from_pdf(file_path)
            tech_summary, layman_story, conclusion = analyzer.analyze_financials(company, report_text)
            visuals = analyzer.generate_visualizations(tech_summary)
            
            # Clean up
            try:
                os.remove(file_path)
            except Exception as e:
                app.logger.error(f"Error deleting file: {str(e)}")

            return render_template("result.html",
                                company=company,
                                tech_summary=tech_summary,
                                layman_story=layman_story,
                                conclusion=conclusion,
                                visuals=visuals)

        except Exception as e:
            app.logger.error(f"Processing error: {str(e)}")
            flash("Error processing file. Please try again.", "error")
            return redirect(url_for("index"))

    flash("Invalid file type. Only PDF files are allowed.", "error")
    return redirect(url_for("index"))

@app.route("/explain_term", methods=["POST"])
def explain_term():
    term = request.form.get("term", "").strip()
    if not term:
        return "Please enter a financial term", 400
    
    try:
        explanation = analyzer.generate_educational_explanation(term)
        return explanation
    except Exception as e:
        app.logger.error(f"Term explanation error: {str(e)}")
        return "Error generating explanation", 500

if __name__ == "__main__":
    app.run(debug=os.environ.get('FLASK_DEBUG') == '1')