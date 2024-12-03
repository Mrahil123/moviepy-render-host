from moviepy.editor import AudioFileClip, ImageClip
import cv2
import numpy as np

def create_portrait_video(image_path, audio_path, output_path, volume=1.0, duration=10):
    """
    Create a portrait video from a still image and audio file using OpenCV.
    """
    try:
        # Read image with OpenCV
        image = cv2.imread(image_path)
        if image is None:
            return False, "Failed to load image"
        
        # Convert BGR to RGB (OpenCV uses BGR by default)
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        # Get target dimensions (9:16 ratio for portrait video)
        target_width = 1080
        target_height = 1920
        
        # Get dimensions of the original image
        src_height, src_width, _ = image.shape
        
        # Calculate scale to fit the image within the portrait frame while maintaining aspect ratio
        scale = min(target_width / src_width, target_height / src_height)
        new_width = int(src_width * scale)
        new_height = int(src_height * scale)
        
        # Resize the image
        resized_image = cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_LANCZOS4)
        
        # Create a black background (canvas) of the portrait size
        canvas = np.zeros((target_height, target_width, 3), dtype=np.uint8)
        
        # Center the resized image on the canvas
        start_x = (target_width - new_width) // 2
        start_y = (target_height - new_height) // 2
        canvas[start_y:start_y + new_height, start_x:start_x + new_width] = resized_image
        
        # Create ImageClip directly from the numpy array
        video = ImageClip(canvas)
        
        # Load audio
        audio = AudioFileClip(audio_path)
        
        # Set the video duration
        video = video.set_duration(duration)
        
        # Adjust audio volume
        audio = audio.volumex(volume)
        
        # Trim or extend audio to match video duration
        if audio.duration > duration:
            audio = audio.subclip(0, duration)
        else:
            audio = audio.set_duration(duration)
        
        # Add audio to video
        final_video = video.set_audio(audio)
        
        # Write final video
        final_video.write_videofile(
            output_path,
            fps=30,
            codec='libx264',
            audio_codec='aac',
            preset='medium'
        )
        
        # Clean up
        video.close()
        audio.close()
        final_video.close()
        
        return True, "Video created successfully!"
    
    except Exception as e:
        return False, f"Error creating video: {str(e)}"

# if __name__ == "__main__":
#     # Example usage
#     image_path = "your_image.png"    # Replace with your image path
#     audio_path = "your_audio.mp3"    # Replace with your audio path
#     output_path = "output_video.mp4" # Replace with desired output path
    
#     success, message = create_portrait_video(
#         image_path, 
#         audio_path, 
#         output_path,
#         volume=1.0,
#         duration=10  # Set fixed duration
#     )
#     print(message)
