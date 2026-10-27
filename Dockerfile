FROM python:3.9-slim

# FFmpeg aur Node.js install karein
RUN apt-get update && apt-get install -y ffmpeg nodejs npm curl

WORKDIR /app

# PO Token Provider ko clone karein aur install karein
RUN git clone https://github.com/Brainicism/bgutil-ytdlp-pot-provider.git /bgutil
WORKDIR /bgutil/server
RUN npm install && npx tsc

# Wapas app folder mein aayen
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

# PO Token server ko background mein start karein aur phir Gunicorn chalayein
CMD ["sh", "-c", "node /bgutil/server/build/main.js & gunicorn app:app --bind 0.0.0.0:10000"]