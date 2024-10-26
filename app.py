from flask import Flask, render_template, request, send_file
import os

app = Flask(__name__)

# Import your comic generation function
from fd import GenerateComic, language_symbols

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/register')
def register():
    return render_template('register.html')

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/generate_comic', methods=['POST'])
def generate_comic():
    topic = request.form['topic']
    style = request.form['style']
    language = request.form['language']
    
    # Get the language symbol for translation
    target_lang = language_symbols.get(language, "en")
    
    # Call your GenerateComic function to generate the comic
    GenerateComic(topic, style, target_lang)
    
    # Return JSON response to indicate the comic generation was successful
    return jsonify({"status": "success"})

# Route to download the latest comic PDF

        return abort(404, description="PDF directory not found")
    
    pdf_files = os.listdir(pdf_directory)
    
    if not pdf_files:
        return abort(404, description="No PDFs found")
    
    # Get the latest file by modification time
   
    if not os.path.exists(latest_pdf):
        return abort(404, description="PDF file not found")
    
    # Send the latest PDF file
    return send_file(latest_pdf, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
