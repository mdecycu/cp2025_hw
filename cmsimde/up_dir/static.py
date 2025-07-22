from flask import Flask, send_from_directory

app = Flask(__name__)

# Route to serve the index.html file
@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

# Route to serve static files from the ./cmsimde/static directory
@app.route('/cmsimde/static/<path:filename>')
def serve_static(filename):
    return send_from_directory('cmsimde/static', filename)

# Route to serve other HTML files from the root directory
@app.route('/<path:filename>')
def serve_html(filename):
    return send_from_directory('.', filename)

if __name__ == '__main__':
    app.run(debug=True)
