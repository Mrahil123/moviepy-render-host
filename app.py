from flask import Flask, request, send_file,jsonify
import chess
from PIL import Image, ImageDraw
from io import BytesIO

import ssl
import requests
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email import encoders

import csv
from random import randrange

from video import create_portrait_video

# main app
def create_app():
    app = Flask(__name__)


    @app.route("/")
    def index():
        return "Hello Rahil Chess World!"
    
    @app.route("/image-to-video", methods=['POST'])
    def imageToVideo():
        image_path = "your_image.png"    # Replace with your image path
        audio_path = "your_audio.mp3"    # Replace with your audio path
        output_path = "output_video.mp4" # Replace with desired output path
        
        success, message = create_portrait_video(
            image_path, 
            audio_path, 
            output_path,
            volume=1.0,
            duration=10  # Set fixed duration
        )
        print(message)
    
    return app

if __name__ == "__main__":
    app = create_app()
    # app.run(port=8000, debug=True)
