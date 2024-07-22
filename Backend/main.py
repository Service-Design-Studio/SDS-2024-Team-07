from flask import Flask, request, jsonify
import vertexai
from vertexai.preview.generative_models import GenerativeModel, Image
from google.oauth2 import service_account
import os
import time
import random

app = Flask(__name__)

PROJECT_ID = "dbsdoccheckteam7"
REGION = "asia-east1"

script_dir = os.path.dirname(os.path.abspath(__file__))
SERVICE_ACCOUNT_FILE = os.path.join(script_dir, 'dbsdoccheckteam7-7b5fc6a831cc.json')

credentials = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE)
vertexai.init(project=PROJECT_ID, location=REGION, credentials=credentials)

UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/')
def index():
    return 'Flask backend is running'

def generate_content_with_backoff(prompt, image, retries=5):
    generative_multimodal_model = GenerativeModel("gemini-1.5-pro-001")
    for i in range(retries):
        try:
            response = generative_multimodal_model.generate_content([prompt, image])
            return response
        except Exception as e:
            if "429" in str(e):
                wait_time = (2 ** i) + random.uniform(0, 1)
                print(f"Rate limit exceeded. Retrying in {wait_time:.2f} seconds...")
                time.sleep(wait_time)
            else:
                raise e
    raise Exception("Maximum retries exceeded")

def process_image_with_prompt(image_file_path, prompt):
    image = Image.load_from_file(image_file_path)
    response = generate_content_with_backoff(prompt, image)
    try:
        result = response.candidates[0].content.parts[0].text.strip().lower()
        return result in ['true', 'false'] and result or 'unknown format'
    except (KeyError, IndexError, AttributeError):
        return 'unknown format'

def upload_and_process_file(file, prompt):
    if file.filename == '':
        return jsonify(result=False, message='No selected file'), 400

    if file:
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(file_path)
        result = process_image_with_prompt(file_path, prompt)
        print(result)
        return jsonify(result=result, message='File processed successfully', file_path=file_path)
    else:
        return jsonify(result=False, message='File upload failed'), 500

@app.route('/upload/passport', methods=['POST'])
def upload_passport():
    prompt = "Is this a passport? Answer with 'True' or 'False'."
    return upload_and_process_file(request.files.get('file'), prompt)

@app.route('/upload/employment_pass', methods=['POST'])
def upload_employment_pass():
    prompt = "Is this an employment pass? Answer with 'True' or 'False'."
    return upload_and_process_file(request.files.get('file'), prompt)

@app.route('/upload/income_tax', methods=['POST'])
def upload_income_tax():
    prompt = "Is this an income tax document? Answer with 'True' or 'False'."
    return upload_and_process_file(request.files.get('file'), prompt)

@app.route('/upload/proof_of_address', methods=['POST'])
def upload_proof_of_address():
    prompt = "Is this a proof of address? Answer with 'True' or 'False'."
    return upload_and_process_file(request.files.get('file'), prompt)

@app.route('/upload/payslip', methods=['POST'])
def upload_payslip():
    prompt = "Is this a payslip? Answer with 'True' or 'False'."
    return upload_and_process_file(request.files.get('file'), prompt)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    app.run(debug=True, host='0.0.0.0', port=port)
