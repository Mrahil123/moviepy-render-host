def create_portrait_video(image_path, audio_path, output_path, volume=1.0, duration=10):
    """
    Create a video from an image and audio file with enhanced error handling
    """
    try:
        from moviepy.editor import ImageClip, AudioFileClip, CompositeVideoClip
        import os

        # Verify input files exist
        if not os.path.exists(image_path):
            return False, f"Image file not found: {image_path}"
        if not os.path.exists(audio_path):
            return False, f"Audio file not found: {audio_path}"

        # Load and verify image clip
        image_clip = ImageClip(image_path)
        if image_clip.size[0] == 0 or image_clip.size[1] == 0:
            return False, "Invalid image dimensions"

        # Load and verify audio clip
        audio_clip = AudioFileClip(audio_path)
        if audio_clip.duration == 0:
            return False, "Invalid audio file duration"

        # Set the duration based on audio length if not specified
        final_duration = min(duration, audio_clip.duration) if duration else audio_clip.duration
        
        # Create the video clip
        video_clip = image_clip.set_duration(final_duration)
        video_clip = video_clip.set_audio(audio_clip.set_duration(final_duration).volumex(volume))

        # Set codec and bitrate parameters for better compatibility
        write_params = {
            'codec': 'libx264',
            'audio_codec': 'aac',
            'temp_audiofile': os.path.join(os.path.dirname(output_path), 'temp-audio.m4a'),
            'remove_temp': True,
            'bitrate': '2000k',
            'fps': 24
        }

        # Write the video file with progress monitoring
        video_clip.write_videofile(
            output_path,
            **write_params,
            logger=None  # Disable progress bar to avoid pipe issues
        )

        # Clean up
        video_clip.close()
        audio_clip.close()
        image_clip.close()

        if not os.path.exists(output_path):
            return False, "Video file was not created successfully"

        return True, "Video created successfully"

    except Exception as e:
        # Clean up any partially created files
        if os.path.exists(output_path):
            try:
                os.remove(output_path)
            except:
                pass
                
        return False, f"Error creating video: {str(e)}"

def create_app():
    app = Flask(__name__)
    
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

            # Create a unique temporary directory
            temp_dir = tempfile.mkdtemp(prefix='video_creation_')
            try:
                image_path = os.path.join(temp_dir, "input_image.png")
                audio_path = os.path.join(temp_dir, "input_audio.mp3")
                output_path = os.path.join(temp_dir, "output_video.mp4")
                
                # Download files with timeout and retries
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

                # Create video with enhanced error handling
                success, message = create_portrait_video(
                    image_path,
                    audio_path,
                    output_path,
                    volume=1.0,
                    duration=10
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
                # Clean up temporary directory
                try:
                    import shutil
                    shutil.rmtree(temp_dir, ignore_errors=True)
                except:
                    pass

        except Exception as e:
            return jsonify({
                "success": False,
                "message": f"Server error: {str(e)}"
            }), 500

    return app
