from flask import Flask, request, jsonify
import os
import tempfile
import requests
import base64
from dotenv import load_dotenv
from video import create_portrait_video  # Import your video creation logic
import urllib3

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Helper function to download a file
def download_file(url, local_path):
    """Download a file from URL and save it locally with better error handling."""
    try:
        # Configure session with longer timeout and SSL verification disabled
        session = requests.Session()
        session.verify = False
        session.timeout = 30

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = session.get(url, headers=headers, stream=True)
        response.raise_for_status()
        
        content_type = response.headers.get('content-type', '')
        if 'image' not in content_type and 'audio' not in content_type:
            raise ValueError(f"Invalid content type: {content_type}")

        with open(local_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        return True, None
    except requests.exceptions.RequestException as e:
        return False, f"Network error: {str(e)}"
    except Exception as e:
        return False, f"Error: {str(e)}"

# Create Flask app
def create_app():
    app = Flask(__name__)
    
    @app.route("/")
    def index():
        return "Hello Rahil Chess World!"
    
    @app.route("/image-to-video", methods=['POST'])
    def imageToVideo():
        try:
            data = request.get_json()
            
            if not data:
                return jsonify({
                    "success": False,
                    "message": "No JSON data received"
                }), 400

            if 'image_url' not in data or 'audio_url' not in data:
                return jsonify({
                    "success": False,
                    "message": "Missing required fields: 'image_url' and/or 'audio_url'"
                }), 400

            # Validate URLs
            if not all(url.startswith(('http://', 'https://')) for url in [data['image_url'], data['audio_url']]):
                return jsonify({
                    "success": False,
                    "message": "Invalid URL format. URLs must start with http:// or https://"
                }), 400

            with tempfile.TemporaryDirectory() as temp_dir:
                image_path = os.path.join(temp_dir, "input_image.png")
                audio_path = os.path.join(temp_dir, "input_audio.mp3")
                output_path = os.path.join(temp_dir, "output_video.mp4")
                
                # Download image
                success, error_message = download_file(data['image_url'], image_path)
                if not success:
                    return jsonify({
                        "success": False,
                        "message": f"Failed to download image: {error_message}",
                        "url": data['image_url']
                    }), 400

                # Download audio
                success, error_message = download_file(data['audio_url'], audio_path)
                if not success:
                    return jsonify({
                        "success": False,
                        "message": f"Failed to download audio: {error_message}",
                        "url": data['audio_url']
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
                    # Encode video in base64
                    with open(output_path, "rb") as video_file:
                        video_base64 = base64.b64encode(video_file.read()).decode('utf-8')
                    
                    return jsonify({
                        "success": True,
                        "message": "Video created successfully",
                        "video": video_base64,
                        "mime_type": "video/mp4"
                    })
                else:
                    return jsonify({
                        "success": False,
                        "message": f"Video creation failed: {message}"
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
