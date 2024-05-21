from flask import Flask, send_from_directory
import os

app = Flask(__name__)

@app.route('/<base_path>/')
def serve_static_index(base_path):
    return send_from_directory("/runtime", 'wasm-index.html')

@app.route('/<base_path>/<path:path>')
def serve_static_files(base_path, path):
    if path == "runtime-loader.js":
        return send_from_directory("/www", f"{base_path}.js")
    return send_from_directory("/www", path)

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=8080)
