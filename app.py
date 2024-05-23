from flask import Flask, render_template, request, redirect, url_for
from pdfminer.high_level import extract_text
import spacy
import re
import os

app = Flask(__name__)

PHONE_REG = re.compile(r'[\+\(]?[1-9][0-9 .\-\(\)]{8,}[0-9]')
EMAIL_REG = re.compile(r'[a-z0-9\.\-+_]+@[a-z0-9\.\-+_]+\.[a-z]+')
nlp = spacy.load("en_core_web_sm")

UPLOADS_DIR = 'uploads'  # Define the directory to store uploaded files

@app.route('/', methods=['GET', 'POST'])
def index():
    if not os.path.exists(UPLOADS_DIR):
        os.makedirs(UPLOADS_DIR)  # Create the uploads directory if it doesn't exist

    if request.method == 'POST':
        uploaded_files = request.files.getlist("pdf_files")  # Get list of uploaded files
        results = []

        for pdf_file in uploaded_files:
            if pdf_file.filename == '':
                continue  # Skip if no file selected
            
            # Save the file to the uploads directory
            pdf_path = os.path.join(UPLOADS_DIR, pdf_file.filename)
            pdf_file.save(pdf_path)

            txt = extract_text_from_pdf(pdf_path)

            name = extract_name(txt)
            emails = extract_emails(txt)
            phone_number = extract_phone_number(txt)
            skills = extract_skills(txt)

            results.append({
                'name': name,
                'emails': emails,
                'phone_number': phone_number,
                'skills': skills
            })

        # Keyword search
        query = request.form.get('query')
        result_from_chat = search_keyword_in_pdfs(UPLOADS_DIR, query)

        # Get list of uploaded PDF filenames
        uploaded_pdfs = [f for f in os.listdir(UPLOADS_DIR) if f.endswith('.pdf')]

        return render_template('index.html', results=results, result_from_chat=result_from_chat, uploaded_pdfs=uploaded_pdfs)
    return render_template('index.html')

@app.route('/clear_uploads', methods=['POST'])
def clear_uploads():
    # Remove all files from the uploads directory
    for file_name in os.listdir(UPLOADS_DIR):
        file_path = os.path.join(UPLOADS_DIR, file_name)
        if os.path.isfile(file_path):
            with open(file_path, 'rb') as f:
                f.close()  # Close the file
            os.remove(file_path)

    # Redirect back to the index page after clearing uploads
    return redirect(url_for('index'))

def extract_text_from_pdf(pdf_path):
    return extract_text(pdf_path)

def extract_phone_number(resume_text):
    phone = re.findall(PHONE_REG, resume_text)
    if phone:
        number = ''.join(phone[0])
        if resume_text.find(number) >= 0 and len(number) < 16:
            return number
    return None

def extract_emails(resume_text):
    return re.findall(EMAIL_REG, resume_text)

def extract_name(resume_text):
    nlp = spacy.load("en_core_web_sm")
    doc = nlp(resume_text)
    person = [token.text for token in doc if token.pos_ == 'PROPN']
    if len(person) >= 2:
        return ' '.join(person[:2])
    return None

def extract_skills(resume_text):
    doc = nlp(resume_text)
    skills = []
    skill_keywords = ['python,flask','python','python,NodeJs', 'HTML', 'html', 'CSS', 'JS', 'js', 'HTML/CSS', 'C/C++', 'java', 'machine learning', 'TAMIL', 'data analysis', 'communication', 'project management', 'teamwork', 'Problem solving', 'Negotiation skills', 'Problem solving', 'C++', 'NodeJs', 'OpenCV', 'Web Developer']
    for token in doc:
        if token.text.lower() in skill_keywords:
            skills.append(token.text)
    return skills

def search_keyword_in_pdfs(directory, query):
    result = []
    if not os.path.exists(directory):
        return result
    
    for filename in os.listdir(directory):
        if filename.endswith(".pdf"):
            pdf_path = os.path.join(directory, filename)
            txt = extract_text_from_pdf(pdf_path)
            if query.lower() in txt.lower():
                result.append(extract_name(txt))  # Assuming name extraction for chat result
    return result

if __name__ == '__main__':
    app.run(debug=True)
