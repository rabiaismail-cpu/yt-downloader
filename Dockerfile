FROM python:3.9-slim

# System dependencies install karein (FFmpeg aur Node.js ke liye)
RUN apt-get update && apt-get install -y ffmpeg nodejs npm git

# App directory banayein
WORKDIR /app

# PO Token Provider ko clone karein aur usko build karein
RUN git clone https://github.com/Brainicism/bgutil-ytdlp-pot-provider.git /bgutil
WORKDIR /bgutil/server
RUN npm install && npx tsc

# Wapas app directory mein aayen
WORKDIR /app

# Python dependencies install karein
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Baqi saara code copy karein
COPY . .

# PO Token server ko background mein chalayein, aur sath hi Gunicorn (Flask) ko start karein
CMD ["sh", "-c", "node /bgutil/server/build/main.js & gunicorn app:app --bind 0.0.0.0:10000"]