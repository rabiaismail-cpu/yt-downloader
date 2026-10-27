from flask import Flask, render_template, request, jsonify, send_file, Response
import yt_dlp
import os
import uuid
import threading
import time

app = Flask(__name__)

# Ye 4 lines Render se cookies utha kar file banayengi
if os.environ.get('YOUTUBE_COOKIES'):
    with open('youtube-cookies.txt', 'w') as f:
        f.write(os.environ.get('YOUTUBE_COOKIES'))

DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# Background mein video download karne ka function (Agar direct link na mile toh)
def download_task(url, filename, download_type):
    try:
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'nocheckcertificate': True,
            'js_runtimes': {'deno': {}},
            'cookiefile': 'youtube-cookies.txt',
            'outtmpl': filename,
            'extractor_args': {'youtube': {'player_client': ['web', 'android']}},
        }
        if download_type == 'audio':
            ydl_opts['format'] = 'bestaudio/best'
        else:
            ydl_opts['format'] = 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best'
            ydl_opts['merge_output_format'] = 'mp4'

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
    except Exception as e:
        print(f"\n🚨 BACKGROUND DOWNLOAD ERROR: {e}\n")

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/download', methods=['POST'])
def download():
    data = request.json
    url = data.get('url')
    download_type = data.get('type', 'video')
    
    if not url:
        return jsonify({'error': 'URL missing'}), 400

    # Video ID nikaalne ki koshish karein (Thumbnail ke liye)
    video_id = ""
    if "v=" in url:
        video_id = url.split("v=")[1].split("&")[0]
    elif "youtu.be/" in url:
        video_id = url.split("youtu.be/")[1].split("?")[0]

    try:
        # STEP 1: Pehle check karein ke kya humein DIRECT LINK mil sakta hai?
        # (Ye bohot fast hota hai aur mostly block nahi hota)
        ydl_opts_direct = {
            'quiet': True,
            'no_warnings': True,
            'nocheckcertificate': True,
            'js_runtimes': {'deno': {}},
            'cookiefile': 'youtube-cookies.txt',
            'extractor_args': {'youtube': {'player_client': ['android', 'ios']}},
        }
        
        if download_type == 'audio':
            ydl_opts_direct['format'] = 'bestaudio/best'
        else:
            ydl_opts_direct['format'] = 'best[ext=mp4]/best'

        with yt_dlp.YoutubeDL(ydl_opts_direct) as ydl:
            info = ydl.extract_info(url, download=False)
            direct_url = None
            
            if 'formats' in info:
                # Aisi file dhoondein jisme video aur audio dono hon
                valid_formats = [f for f in info['formats'] if f.get('vcodec') != 'none' and f.get('acodec') != 'none']
                if valid_formats:
                    direct_url = valid_formats[-1].get('url')

            if direct_url:
                # Agar direct link mil gaya, toh foran user ko bhej dein!
                return jsonify({
                    'success': True, 
                    'type': 'direct',
                    'download_url': direct_url,
                    'thumbnail': f'https://img.youtube.com/vi/{video_id}/mqdefault.jpg' if video_id else ''
                })

    except Exception as e:
        print(f"Direct Link Check Failed: {e}. Falling back to server download...")

    # STEP 2: Agar direct link nahi mila, toh Server par download karein
    unique_id = str(uuid.uuid4())[:6]
    filename = os.path.join(DOWNLOAD_DIR, f'{unique_id}.mp4')

    thread = threading.Thread(target=download_task, args=(url, filename, download_type))
    thread.daemon = True
    thread.start()

    return jsonify({
        'success': True, 
        'type': 'server',
        'download_url': f'/get_file/{os.path.basename(filename)}',
        'thumbnail': f'https://img.youtube.com/vi/{video_id}/mqdefault.jpg' if video_id else ''
    })

@app.route('/get_file/<filename>')
def get_file(filename):
    filepath = os.path.join(DOWNLOAD_DIR, filename)
    
    # Server par download hone ka wait karein
    for _ in range(90): # 90 seconds tak wait karega
        if os.path.exists(filepath) and os.path.getsize(filepath) > 0:
            # File ready hai
            time.sleep(1) # Ek second ruk kar file ko complete hone dein
            break
        time.sleep(1)

    if os.path.exists(filepath):
        return send_file(filepath, as_attachment=True)
    
    # Agar file nahi bani, toh error page return karein
    return """
    <html>
        <body style="text-align: center; padding-top: 50px; font-family: sans-serif;">
            <h2 style="color: red;">Download Failed</h2>
            <p>YouTube blocked the server download. Please try again or use a different video.</p>
            <a href="/" style="padding: 10px 20px; background: #007bff; color: white; text-decoration: none; border-radius: 5px;">Go Back</a>
        </body>
    </html>
    """, 404

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=True)