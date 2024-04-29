from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask import Flask, render_template, send_from_directory
import pandas as pd
import os
from google.cloud import storage

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "within-merlin-146bb0e8740c.json"
BUCKET_NAME = 'dev-ad-score-bucket'

from werkzeug.utils import secure_filename
import google.cloud.storage as gcs

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['GCS_BUCKET'] = BUCKET_NAME


os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

client = gcs.Client()
bucket = client.bucket(app.config['GCS_BUCKET'])

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return redirect(request.url)
    file = request.files['file']
    if file.filename == '':
        return redirect(request.url)
    if file:
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        return redirect(url_for('edit_file', filename=filename))

@app.route('/view/<filename>')
def edit_file(filename):
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    try:
        data = pd.read_csv(file_path)
        csv_json = data.to_json(orient='records')
    except Exception as e:
        return str(e), 500
    
    return render_template('view.html', csv_data=csv_json, filename=filename)

# @app.route('/save/<filename>', methods=['POST'])
# def save_file(filename):
#     content = request.form['data']
#     local_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
#     with open(local_path, 'w') as f:
#         f.write(content)

    
#     blob = bucket.blob(filename)
#     blob.upload_from_filename(local_path)

#     return redirect(url_for('edit_file', filename=filename))
from datetime import datetime
@app.route('/save/<filename>', methods=['POST'])
def save_file(filename):
    # Get the current date and time
    date_time = datetime.now().strftime("%Y%m%d%H%M%S")
    new_filename = f"{os.path.splitext(filename)[0]}_{date_time}.csv"
    
    content = request.form['data']
    local_path = os.path.join(app.config['UPLOAD_FOLDER'], new_filename)

    # Write the data to a local file
    with open(local_path, 'w') as f:
        f.write(content)

    # Upload to Google Cloud Storage
    bucket = storage.Client().get_bucket('your-bucket-name')  # Make sure to set your actual bucket name
    blob = bucket.blob(new_filename)
    blob.upload_from_filename(local_path)

    return redirect(url_for('edit_file', filename=new_filename))


storage_client = storage.Client()
bucket_name = BUCKET_NAME  
import csv

from flask import Flask, request, jsonify
import csv
from datetime import datetime
from google.cloud import storage
import os


@app.route('/save', methods=['POST'])
def save_changes():
    try:
        data = request.get_json()['data']
        if not data or not isinstance(data[0], list):
            return jsonify({"error": "Invalid data format"}), 400

        headers = request.get_json().get('headers', [])
        original_filename = 'edited_data'
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f'uploads/{original_filename}_{timestamp}.csv'

        with open(filename, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(headers)  # Write the header information
            writer.writerows(data)

        # Assuming 'bucket_name' is defined somewhere globally or retrieved from a config
        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(filename)
        blob.upload_from_filename(filename)

        os.remove(filename)
        
        return jsonify({"message": "Data saved successfully to Google Cloud Storage with headers!"})
    except Exception as e:
        app.logger.error(f"Error saving data: {str(e)}")
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True)
