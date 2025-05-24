from flask import Flask, request, send_file, abort, send_from_directory, after_this_request
import os
import tempfile
from yt_dlp import YoutubeDL
import shutil

app = Flask(__name__, static_folder=None, template_folder=None)

@app.route('/custom/<path:filename>')
def custom_static(filename):
    return send_from_directory('Custom', filename)

@app.route('/')
@app.route('/index.html')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/<platform>/')
@app.route('/<platform>/index.html')
def platform_page(platform):
    if platform in ['youtube', 'tiktok', 'instagram']:
        return send_from_directory(platform, 'index.html')
    abort(404)

@app.route('/download/<platform>', methods=['POST'])
def download(platform):
    url = request.form.get('url')
    dtype = request.form.get('type', 'video')
    if not url:
        abort(400)
    return process_download(url, dtype)

def process_download(url, dtype):
    tmp_dir = tempfile.mkdtemp()
    output_path = os.path.join(tmp_dir, '%(id)s.%(ext)s')
    ffmpeg_path = "C:/ffmpeg/bin"
    opts = {
        'outtmpl': output_path,
        'merge_output_format': 'mp4',
        'quiet': True,
        'noplaylist': True,
        'ignoreerrors': False,
        'ffmpeg_location': ffmpeg_path
    }

    if dtype == 'mp3':
        opts['format'] = 'bestaudio/best'
        opts['postprocessors'] = [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }]
    else:
        opts['format'] = 'bv[ext=mp4][vcodec*=avc1]+ba/b[ext=mp4][vcodec*=avc1]/b'

    with YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=True)
        ext = 'mp3' if dtype == 'mp3' else info.get('ext', 'mp4')
        filename = f"{info['id']}.{ext}"
        filepath = os.path.join(tmp_dir, filename)
        if not os.path.exists(filepath):
            shutil.rmtree(tmp_dir)
            abort(404, description="File not found after download")

    return serve_file(filepath, tmp_dir)

def serve_file(path, tmp_dir):
    @after_this_request
    def cleanup(response):
        try:
            shutil.rmtree(tmp_dir)
        except Exception:
            pass
        return response
    return send_file(path, as_attachment=True)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
