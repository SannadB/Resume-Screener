import os
import openai
import pdfplumber
import csv
from flask import Flask, request, jsonify, render_template, send_file
from werkzeug.utils import secure_filename
from resume_screener_pack.llama_index.packs.resume_screener.base import ResumeScreenerPack
from resume_screener import ResumeScreenerGPT
from resume_screener_models import ResumeScreenerDecision
import json
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
openai.api_key = os.getenv('OPEN_AI_KEY')

results = []

def chat_gpt(conversation):
    response = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=conversation
    )
    return response.choices[0].message.content

def pdf_to_text(file_path):
    text = ''
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            text += page.extract_text()
    return text

def update_csv(results):
    with open('results.csv', 'w', newline='') as csvfile:
        csv_writer = csv.writer(csvfile)
        csv_writer.writerow(["Resume Name", "Name", "E-Mail", "Contact", "Experience", "Score", "Description"])
        csv_writer.writerows(results)

@app.route('/upload', methods=['GET', 'POST'])
def upload_resume():
    global results
    if request.method == 'POST':
        model = request.form['model']
        resume_files = request.files.getlist('file[]')
        job_description = request.form['job_description']
        job_criteria = request.form['job_criteria']
        job_criteria_list = [criteria.strip() for criteria in job_criteria.split('\n')]
        print("here")
        print(model)
        file_paths = []

        for resume_file in resume_files:
            if resume_file and resume_file.filename:
                # Save the file to a temporary location
                temp_dir = 'uploads'
                if not os.path.exists(temp_dir):
                    os.makedirs(temp_dir)
                file_path = os.path.join(temp_dir, resume_file.filename)
                resume_file.save(file_path)
                
                # Add the file path to the list
                file_paths.append(file_path)
        
        results = []
        if model == "GPT":
            screener = ResumeScreenerGPT(job_description, job_criteria_list)
            source = "GPT"
            for resume_file in file_paths:
                result = screener.screen_resume(resume_file)
                print(result)
                results.append([resume_file, result.candidate_name, result.candidate_email, result.candidate_phone, result.overall_reasoning, result.overall_score, source])
        elif model == "LLAMA":
            screener = ResumeScreenerPack(job_description, job_criteria_list)
            source = "LLAMA"
            for resume_file in file_paths:
                print(resume_file)
                response = screener.run(resume_path=resume_file)
                print(response)
                results.append([resume_file, response.candidate_name, response.candidate_email, response.candidate_phone, response.overall_reasoning, response.overall_score, source])

        return jsonify({"results": results})
    else:  # Handling the GET request
        return render_template('upload.html')

@app.route('/download_csv', methods=['GET'])
def download_csv():
    global results
    update_csv(results)
    return send_file('results.csv', as_attachment=True)

@app.route('/')
def index():
    return render_template('upload.html')

if __name__ == '__main__':
    app.run()
