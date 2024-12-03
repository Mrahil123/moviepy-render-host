from flask import Flask, request, send_file, jsonify
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
import os
import tempfile
import base64
from dotenv import load_dotenv
from video import create_portrait_video

# Load environment variables
load_dotenv()

def create_app():
    app = Flask(__name__)
    
    @app.route("/")
    def index():
        return "Hello Rahil Chess World!"
    
    @app.route("/image-to-video", methods=['POST'])
    def imageToVideo():
        try:
            # Get JSON data from request
            data = request.get_json()
            
            if not data:
                return jsonify({
                    "success": False,
                    "message": "No JSON data received"
                }), 400

            # Check for required fields
            if 'image' not in data or 'audio' not in data:
                return jsonify({
                    "success": False,
                    "message": "Missing required fields: 'image' and/or 'audio'"
                }), 400

            # Create temporary directory
            with tempfile.TemporaryDirectory() as temp_dir:
                # Create temporary file paths
                image_path = os.path.join(temp_dir, "input_image.png")
                audio_path = os.path.join(temp_dir, "input_audio.mp3")
                output_path = os.path.join(temp_dir, "output_video.mp4")
                
                try:
                    # Decode and save image
                    image_data = base64.b64decode(data['image'])
                    with open(image_path, 'wb') as f:
                        f.write(image_data)

                    # Decode and save audio
                    audio_data = base64.b64decode(data['audio'])
                    with open(audio_path, 'wb') as f:
                        f.write(audio_data)

                    # Create video
                    success, message = create_portrait_video(
                        image_path,
                        audio_path,
                        output_path,
                        volume=1.0,
                        duration=10
                    )
                    
                    if success and os.path.exists(output_path):
                        # Read the output video and convert to base64
                        with open(output_path, 'rb') as f:
                            video_data = base64.b64encode(f.read()).decode('utf-8')
                        
                        return jsonify({
                            "success": True,
                            "video": video_data
                        })
                    else:
                        return jsonify({
                            "success": False,
                            "message": f"Video creation failed: {message}"
                        }), 500

                except base64.binascii.Error:
                    return jsonify({
                        "success": False,
                        "message": "Invalid base64 encoding in image or audio data"
                    }), 400
                        
                except Exception as e:
                    return jsonify({
                        "success": False,
                        "message": f"Error during video creation: {str(e)}"
                    }), 500

        except Exception as e:
            return jsonify({
                "success": False,
                "message": f"Server error: {str(e)}"
            }), 500

    return app

# Create the app instance
app = create_app()

if __name__ == "__main__":
    port = int(os.getenv('PORT', 4000))
    debug = os.getenv('DEBUG', 'False').lower() == 'true'
    
    app.run(
        host='0.0.0.0',
        port=port,
        debug=debug
    )
