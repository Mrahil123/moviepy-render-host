from flask import Flask, request, jsonify
import requests
import base64
from io import BytesIO
from video import create_portrait_video  # Import your video creation logic
import urllib3

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Helper function to download a file and return in-memory bytes
def download_file_to_memory(url):
    """Download a file from URL and return its content as bytes."""
    try:
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
        
        return BytesIO(response.content), None
    except requests.exceptions.RequestException as e:
        return None, f"Network error: {str(e)}"
    except Exception as e:
        return None, f"Error: {str(e)}"

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

            # Download files into memory
            image_file, error_message = download_file_to_memory(data['image_url'])
            if not image_file:
                return jsonify({
                    "success": False,
                    "message": f"Failed to download image: {error_message}",
                    "url": data['image_url']
                }), 400

            audio_file, error_message = download_file_to_memory(data['audio_url'])
            if not audio_file:
                return jsonify({
                    "success": False,
                    "message": f"Failed to download audio: {error_message}",
                    "url": data['audio_url']
                }), 400

            # Create video in memory
            output_buffer = BytesIO()
            success, message = create_portrait_video(
                image_file,
                audio_file,
                output_buffer,
                volume=1.0,
                duration=10
            )
            
            if success:
                # Encode video in base64
                output_buffer.seek(0)
                video_base64 = base64.b64encode(output_buffer.read()).decode('utf-8')
                
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
