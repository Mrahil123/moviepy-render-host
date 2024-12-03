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
from dotenv import load_dotenv
from video import create_portrait_video

# Load environment variables
load_dotenv()

def download_file(url, local_path):
    """Download a file from URL and save it locally"""
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()  # Raise an error for bad status codes
        
        with open(local_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        return True
    except Exception as e:
        print(f"Error downloading file from {url}: {str(e)}")
        return False

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

            # Check for required URLs
            if 'image_url' not in data or 'audio_url' not in data:
                return jsonify({
                    "success": False,
                    "message": "Missing required fields: 'image_url' and/or 'audio_url'"
                }), 400

            # Create temporary directory
            with tempfile.TemporaryDirectory() as temp_dir:
                # Create temporary file paths
                image_path = os.path.join(temp_dir, "input_image.png")
                audio_path = os.path.join(temp_dir, "input_audio.mp3")
                output_path = os.path.join(temp_dir, "output_video.mp4")
                
                try:
                    # Download image
                    if not download_file(data['image_url'], image_path):
                        return jsonify({
                            "success": False,
                            "message": "Failed to download image from URL"
                        }), 400

                    # Download audio
                    if not download_file(data['audio_url'], audio_path):
                        return jsonify({
                            "success": False,
                            "message": "Failed to download audio from URL"
                        }), 400

                    # Create video
                    success, message = create_portrait_video(
                        image_path,
                        audio_path,
                        output_path,
                        volume=1.0,
                        duration=10
                    )
                    
                    if success and os.path.exists(output_path):
                        # Read and return the video file
                        return send_file(
                            output_path,
                            mimetype='video/mp4',
                            as_attachment=True,
                            download_name='output_video.mp4'
                        )
                    else:
                        return jsonify({
                            "success": False,
                            "message": f"Video creation failed: {message}"
                        }), 500

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
