from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from datetime import datetime
import PyPDF2
import json
import ssl
import urllib3
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# DISABLE SSL VERIFICATION (for development only)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
ssl._create_default_https_context = ssl._create_unverified_context

# Get API key from environment FIRST
api_key = os.getenv('OPENAI_API_KEY')

if not api_key:
    print("❌ ERROR: OPENAI_API_KEY not found in .env file")
    print("Please create .env file with: OPENAI_API_KEY=sk-your-key-here")
    exit(1)

# Import and initialize OpenAI AFTER getting the key
try:
    from openai import OpenAI
    # Initialize client with api_key as environment variable (not parameter)
    os.environ['OPENAI_API_KEY'] = api_key  # Set it in environment
    client = OpenAI()  # Uses OPENAI_API_KEY from environment
except Exception as e:
    print(f"❌ Error initializing OpenAI client: {str(e)}")
    print("This is usually a version compatibility issue.")
    print("Try: pip install -r requirements_FIXED.txt")
    exit(1)

app = Flask(__name__)
CORS(app)

# Configuration
UPLOAD_FOLDER = 'uploads'
SUMMARIES_FILE = 'summaries.json'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB limit


def load_summaries():
    """Load summaries from JSON file"""
    if os.path.exists(SUMMARIES_FILE):
        try:
            with open(SUMMARIES_FILE, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {}
    return {}


def save_summaries(summaries):
    """Save summaries to JSON file"""
    try:
        with open(SUMMARIES_FILE, 'w') as f:
            json.dump(summaries, f, indent=2)
    except Exception as e:
        print(f"Error saving summaries: {str(e)}")


def extract_text_from_pdf(filepath):
    """Extract text from PDF file"""
    text = ""
    try:
        with open(filepath, 'rb') as f:
            pdf_reader = PyPDF2.PdfReader(f)
            num_pages = len(pdf_reader.pages)
            print(f"📄 Extracting text from {num_pages} pages...")
            
            for page_num, page in enumerate(pdf_reader.pages):
                try:
                    extracted = page.extract_text()
                    if extracted:
                        text += extracted
                    print(f"   Page {page_num + 1}/{num_pages} ✓")
                except Exception as e:
                    print(f"   Page {page_num + 1}/{num_pages} ✗ (skipped)")
    except Exception as e:
        print(f"❌ PDF extraction error: {str(e)}")
    
    return text


def generate_summary(text):
    """Generate summary using OpenAI API"""
    try:
        if not text or len(text.strip()) == 0:
            return "Could not extract text from PDF"
        
        print(f"📤 Sending text to OpenAI ({len(text)} chars)...")
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful assistant that summarizes documents concisely in 3-5 sentences."
                },
                {
                    "role": "user",
                    "content": f"Please summarize this text in 3-5 sentences:\n\n{text[:2000]}"
                }
            ],
            max_tokens=300,
            temperature=0.5
        )
        
        summary = response.choices[0].message.content
        print(f"✅ Summary generated successfully!")
        return summary
        
    except Exception as e:
        error_msg = str(e)
        print(f"❌ OpenAI error: {error_msg}")
        return f"Error: {error_msg}"


@app.route('/upload', methods=['POST'])
def upload_files():
    """Handle file uploads and generate summaries"""
    try:
        if 'files' not in request.files:
            return jsonify({'status': 'error', 'message': 'No files provided'}), 400
        
        files = request.files.getlist('files')
        if not files or files[0].filename == '':
            return jsonify({'status': 'error', 'message': 'No files selected'}), 400
        
        uploaded_data = []
        summaries = load_summaries()
        
        print(f"\n📥 Uploading {len(files)} file(s)...")
        
        for file in files:
            if file and file.filename.endswith('.pdf'):
                print(f"\n📋 Processing: {file.filename}")
                
                # Save file with timestamp
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_')
                filename = timestamp + file.filename
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                print(f"   Saved to: {filepath}")
                
                # Extract text from PDF
                pdf_text = extract_text_from_pdf(filepath)
                
                # Generate summary using OpenAI
                summary = generate_summary(pdf_text) if pdf_text else "Could not extract text"
                
                # Get file info
                file_size = os.path.getsize(filepath)
                file_id = filename.replace('.pdf', '')
                
                # Store summary
                summaries[file_id] = {
                    'original_name': file.filename,
                    'saved_name': filename,
                    'size_bytes': file_size,
                    'size_mb': round(file_size / (1024 * 1024), 2),
                    'upload_time': datetime.now().isoformat(),
                    'summary': summary,
                    'text_length': len(pdf_text)
                }
                
                uploaded_data.append(summaries[file_id])
                print(f"✅ {file.filename} processed successfully!")
        
        # Save summaries to file
        save_summaries(summaries)
        print(f"\n✅ All files processed and saved!")
        
        return jsonify({
            'status': 'success',
            'message': f'Successfully processed {len(uploaded_data)} file(s)',
            'files': uploaded_data,
            'total_files': len(uploaded_data),
            'upload_timestamp': datetime.now().isoformat()
        }), 200
    
    except Exception as e:
        error_msg = str(e)
        print(f"❌ Upload error: {error_msg}")
        return jsonify({'status': 'error', 'message': error_msg}), 500


@app.route('/summaries', methods=['GET'])
def get_summaries():
    """Get all file summaries"""
    try:
        summaries = load_summaries()
        
        summary_list = []
        for file_id, data in summaries.items():
            summary_list.append({
                'id': file_id,
                'filename': data['original_name'],
                'summary': data['summary'],
                'upload_time': data['upload_time'],
                'size_mb': data['size_mb']
            })
        
        return jsonify({
            'status': 'success',
            'total_summaries': len(summary_list),
            'summaries': summary_list
        }), 200
    
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/summary/<file_id>', methods=['GET'])
def get_summary(file_id):
    """Get specific file summary"""
    try:
        summaries = load_summaries()
        
        if file_id in summaries:
            return jsonify({
                'status': 'success',
                'data': summaries[file_id]
            }), 200
        else:
            return jsonify({'status': 'error', 'message': 'Summary not found'}), 404
    
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/files', methods=['GET'])
def get_files():
    """Get list of uploaded files"""
    try:
        files = os.listdir(app.config['UPLOAD_FOLDER'])
        file_info = []
        
        for filename in files:
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            if os.path.isfile(filepath):
                file_size = os.path.getsize(filepath)
                file_info.append({
                    'filename': filename,
                    'size_bytes': file_size,
                    'size_mb': round(file_size / (1024 * 1024), 2)
                })
        
        return jsonify({
            'status': 'success',
            'total_files': len(file_info),
            'files': file_info
        }), 200
    
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/health', methods=['GET'])
def health():
    """Check API health"""
    return jsonify({'status': 'healthy', 'message': 'API is running'}), 200


@app.route('/', methods=['GET'])
def home():
    """Home route with API info"""
    return jsonify({
        'message': 'Document Upload & Summarization API',
        'version': '2.0',
        'endpoints': {
            'POST /upload': 'Upload PDF and generate summary',
            'GET /summaries': 'Get all summaries',
            'GET /summary/:id': 'Get specific summary',
            'GET /files': 'Get list of files',
            'GET /health': 'Check API health'
        }
    }), 200


if __name__ == '__main__':
    print('='*60)
    print('🚀 API Server Starting...')
    print('='*60)
    print('📁 Upload folder:', os.path.abspath(UPLOAD_FOLDER))
    print('🔑 OpenAI API loaded from .env')
    print('🌐 Running on http://localhost:5000')
    print('='*60 + '\n')
    app.run(debug=True, host='localhost', port=5000)
