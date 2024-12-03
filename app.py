from flask import Flask, request, send_file, jsonify
from PIL import Image, ImageDraw
from io import BytesIO
import ssl
import requests
import os
import tempfile
from dotenv import load_dotenv
from video import create_portrait_video  # Import your existing function
import urllib3

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def download_file(url, local_path):
    """Download a file from URL and save it locally with better error handling"""
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

def validate_urls(image_url, audio_url):
    """Validate the format of input URLs"""
    if not all(url.startswith(('http://', 'https://')) for url in [image_url, audio_url]):
        return False, "Invalid URL format. URLs must start with http:// or https://"
    return True, None

def create_app():
    """Create and configure the Flask application"""
    app = Flask(__name__)
    
    @app.route("/")
    def index():
        return "Video Creation Service"
    
    @app.route("/health")
    def health():
        return jsonify({"status": "healthy"}), 200
    
    @app.route("/image-to-video", methods=['POST'])
    def image_to_video():
        temp_dir = None
        try:
            # Validate input JSON
            data = request.get_json()
            if not data:
                return jsonify({
                    "success": False,
                    "message": "No JSON data received"
                }), 400

            # Check required fields
            if 'image_url' not in data or 'audio_url' not in data:
                return jsonify({
                    "success": False,
                    "message": "Missing required fields: 'image_url' and/or 'audio_url'"
                }), 400

            # Validate URL format
            valid, error_message = validate_urls(data['image_url'], data['audio_url'])
            if not valid:
                return jsonify({
                    "success": False,
                    "message": error_message
                }), 400

            # Create a unique temporary directory
            temp_dir = tempfile.mkdtemp(prefix='video_creation_')
            
            try:
                # Set up file paths
                image_path = os.path.join(temp_dir, "input_image.png")
                audio_path = os.path.join(temp_dir, "input_audio.mp3")
                output_path = os.path.join(temp_dir, "output_video.mp4")
                
                # Download files
                for file_url, local_path, file_type in [
                    (data['image_url'], image_path, 'image'),
                    (data['audio_url'], audio_path, 'audio')
                ]:
                    success, error_message = download_file(file_url, local_path)
                    if not success:
                        return jsonify({
                            "success": False,
                            "message": f"Failed to download {file_type}: {error_message}",
                            "url": file_url
                        }), 400

                # Get optional parameters
                duration = data.get('duration', 10)  # Default duration of 10 seconds
                volume = data.get('volume', 1.0)     # Default volume of 1.0

                # Create video using your existing function
                success, message = create_portrait_video(
                    image_path,
                    audio_path,
                    output_path,
                    volume=volume,
                    duration=duration
                )
                
                if success and os.path.exists(output_path):
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

            finally:
                # Clean up temporary directory in the inner try block
                if temp_dir and os.path.exists(temp_dir):
                    try:
                        import shutil
                        shutil.rmtree(temp_dir, ignore_errors=True)
                    except Exception as e:
                        app.logger.error(f"Failed to clean up temporary directory: {str(e)}")

        except Exception as e:
            return jsonify({
                "success": False,
                "message": f"Server error: {str(e)}"
            }), 500

    return app

# Create the app instance
app = create_app()

if __name__ == "__main__":
    # Load environment variables
    load_dotenv()
    
    # Get configuration from environment
    port = int(os.getenv('PORT', 4000))
    debug = os.getenv('DEBUG', 'False').lower() == 'true'
    
    # Run the application
    app.run(
        host='0.0.0.0',
        port=port,
        debug=debug
    )
