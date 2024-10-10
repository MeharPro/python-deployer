import os
from flask import Flask, render_template, request, jsonify, redirect, url_for
import sys
from io import StringIO
import contextlib

app = Flask(__name__)

DEPLOYMENT_DIR = 'deployments'

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/deploy', methods=['POST'])
def deploy():
    code = request.form['code']
    filename = request.form['filename']
    
    if not filename.endswith('.py'):
        filename += '.py'
    
    filepath = os.path.join(DEPLOYMENT_DIR, filename)
    
    # Ensure the filename is unique
    counter = 1
    while os.path.exists(filepath):
        name, ext = os.path.splitext(filename)
        filepath = os.path.join(DEPLOYMENT_DIR, f"{name}_{counter}{ext}")
        counter += 1
    
    # Save the code to the file
    with open(filepath, 'w') as f:
        f.write(code)
    
    return redirect(url_for('view_code', filename=os.path.basename(filepath)))

@app.route('/<filename>')
def view_code(filename):
    filepath = os.path.join(DEPLOYMENT_DIR, filename)
    if not os.path.exists(filepath):
        return "File not found", 404
    
    with open(filepath, 'r') as f:
        code = f.read()
    
    return render_template('shell.html', filename=filename, code=code)

@app.route('/run/<filename>', methods=['POST'])
def run_code(filename):
    filepath = os.path.join(DEPLOYMENT_DIR, filename)
    if not os.path.exists(filepath):
        return jsonify({'output': 'File not found'}), 404

    with open(filepath, 'r') as f:
        code = f.read()

    user_input = request.json['input']

    # Capture stdout and stderr
    output = StringIO()
    input_iterator = iter([user_input])

    def custom_input(prompt=""):
        print(prompt, end='', flush=True)
        try:
            value = next(input_iterator)
            print(value)
            return value
        except StopIteration:
            raise EOFError("No more input")

    with contextlib.redirect_stdout(output), contextlib.redirect_stderr(output):
        try:
            exec(code, {'input': custom_input})
        except Exception as e:
            print(f"Error: {str(e)}")

    return jsonify({'output': output.getvalue()})

if __name__ == '__main__':
    os.makedirs(DEPLOYMENT_DIR, exist_ok=True)
    app.run(debug=True)
