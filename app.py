from flask import Flask, render_template, request, jsonify
import yt_dlp
import os

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/download', methods=['POST'])
def download():
    data = request.json
    url = data.get('url')
    download_type = data.get('type', 'video')
    
    if not url:
        return jsonify({'error': 'URL missing hai!'}), 400

    try:
        # Base settings for yt-dlp
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'nocheckcertificate': True,
            'js_runtimes': {'deno': {}},
        }

        # Format select karein based on type
        if download_type == 'audio':
            ydl_opts['format'] = 'bestaudio/best'
        else:
            ydl_opts['format'] = 'best[ext=mp4]/best'

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            video_url = info.get('url')
            
            if not video_url and 'formats' in info:
                formats = [f for f in info['formats'] if f.get('url')]
                if formats:
                    video_url = formats[-1]['url']

            if video_url:
                return jsonify({'success': True, 'download_url': video_url})
            else:
                return jsonify({'error': 'Direct link nahi mila. Doosri video try karein.'}), 500

    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Render par deploy karne ke liye port setting
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=True)