"""
Talking Head Generation Module using Heygen API

This module handles the generation of AI talking head videos using the Heygen API
and the integration with existing B-roll videos in a split screen format.
"""

import os
import time
import logging
import requests
import dotenv
import json
from moviepy.editor import VideoFileClip, AudioFileClip, CompositeVideoClip
from dotenv import load_dotenv

load_dotenv()

# Heygen API configuration
HEYGEN_GENERATE_URL = "https://api.heygen.com/v2/video/generate"
HEYGEN_STATUS_URL = "https://api.heygen.com/v1/video_status.get"

# Default avatar settings
DEFAULT_AVATAR_ID = "Annie_expressive7_public" 
DEFAULT_VOICE_ID = "f772a099cbb7421eb0176240c611fc43"  # Default voice ID
def generate_heygen_talking_head(script, temp_dir, avatar_id=None, voice_id=None):
    """
    Generate a talking head video using Heygen API
    
    Args:
        script (str): The text script for the talking head to speak
        temp_dir (str): Temporary directory to store files
        avatar_id (str, optional): Heygen avatar ID to use
        voice_id (str, optional): Voice ID to use for speech
        
    Returns:
        str: Path to the downloaded talking head video file
    """
    logging.info("Generating Heygen talking head video")
    
    # Use defaults if not provided
    if not avatar_id:
        avatar_id = DEFAULT_AVATAR_ID
        
    if not voice_id:
        voice_id = DEFAULT_VOICE_ID
    
    # Configure the payload for Heygen API
    payload = {
        "caption": False,
        "dimension": {
            "width": 1280,
            "height": 720
        },
        "video_inputs": [{
            "character": {
                "type": "avatar",
                "avatar_id": avatar_id,
                "scale": 1,
                "avatar_style": "normal"
            },
            "voice": {
                "type": "text",
                "voice_id": voice_id,
                "input_text": script,
                "speed": 1.0,
                "pitch": 0
            },
        }]
    }
    
    headers = {
        "content-type": "application/json",
        "x-api-key": os.environ.get("HEYGEN_API_KEY"),
    }
    
    try:
        # Make the API call to generate the video
        response = requests.post(HEYGEN_GENERATE_URL, json=payload, headers=headers)
        response.raise_for_status()
        
        print("PARESH",response.json())
        
        response_data = response.json()
        logging.debug(f"Heygen API response: {json.dumps(response_data, indent=2)}")
        
        video_id = response_data.get("data", {}).get("video_id")
        
        if not video_id:
            raise Exception("Failed to get video_id from Heygen API response")
        
        logging.info(f"Heygen video generation initiated with video_id: {video_id}")
        
        # Poll for video completion
        status_params = {"video_id": video_id}
        
        video_url = None
        max_attempts = 60  # 10 minutes with 10-second intervals
        
        for attempt in range(max_attempts):
            time.sleep(10)  # Wait 10 seconds between polls
            
            status_response = requests.get(HEYGEN_STATUS_URL, headers=headers, params=status_params)
            status_response.raise_for_status()
            
            status_data = status_response.json()
            status = status_data.get("data", {}).get("status")
            
            logging.info(f"Heygen video status (attempt {attempt+1}/{max_attempts}): {status}")
            
            if status == "completed":
                video_url = status_data.get("data", {}).get("video_url")
                break
            elif status == "failed":
                error = status_data.get("data", {}).get("error")
                raise Exception(f"Heygen video generation failed: {error}")
        
        if not video_url:
            raise Exception("Timed out waiting for Heygen video to complete")
        
        # Download the video
        talking_head_path = os.path.join(temp_dir, "heygen_talking_head.mp4")
        download_response = requests.get(video_url)
        download_response.raise_for_status()
        
        with open(talking_head_path, "wb") as f:
            f.write(download_response.content)
        
        logging.info(f"Successfully downloaded Heygen talking head video to {talking_head_path}")
        return talking_head_path
        
    except Exception as e:
        logging.error(f"Error generating Heygen talking head: {str(e)}")
        raise

def combine_broll_with_talking_head(broll_path, talking_head_path, output_path, temp_dir):
    """
    Combine B-roll video with talking head video in a split screen layout
    
    Args:
        broll_path (str): Path to the B-roll video
        talking_head_path (str): Path to the talking head video
        output_path (str): Path for the output combined video
        temp_dir (str): Temporary directory to store intermediate files
        
    Returns:
        str: Path to the final combined video
    """
    logging.info("Combining B-roll with talking head video")
    
    try:
        # Extract audio from talking head to ensure synchronization
        talking_head_audio_path = os.path.join(temp_dir, "talking_head_audio.mp3")
        talking_head_clip = VideoFileClip(talking_head_path)
        talking_head_clip.audio.write_audiofile(talking_head_audio_path)
        
        # Load the B-roll video
        broll_clip = VideoFileClip(broll_path)
        broll_clip = broll_clip.without_audio()
        
        # Determine final duration (use the shorter of the two)
        final_duration = min(broll_clip.duration, talking_head_clip.duration)
        
        # Trim both clips to the same duration
        broll_clip = broll_clip.subclip(0, final_duration)
        talking_head_clip = talking_head_clip.subclip(0, final_duration)
        
        # Resize videos to fit in split screen (upper half and lower half)
        # Assuming 1280x720 output resolution
        broll_clip = broll_clip.resize(width=1280, height=360)  # Top half
        talking_head_clip = talking_head_clip.resize(width=1280, height=360)  # Bottom half
        
        # Calculate positions (B-roll on top, talking head at bottom)
        broll_position = (0, 0)
        talking_head_position = (0, 360)
        
        # Set positions
        broll_clip = broll_clip.set_position(broll_position)
        talking_head_clip = talking_head_clip.set_position(talking_head_position)
        
        # Add audio from talking head
        final_audio = AudioFileClip(talking_head_audio_path).subclip(0, final_duration)
        
        # Create final composite with both videos
        composite_clip = CompositeVideoClip(
            [broll_clip, talking_head_clip], 
            size=(1280, 720)
        )
        
        # Set audio
        composite_clip = composite_clip.set_audio(final_audio)
        
        # Write final video
        composite_clip.write_videofile(
            output_path, 
            codec="libx264", 
            audio_codec="aac", 
            fps=30, 
            threads=4
        )
        
        # Clean up clips
        broll_clip.close()
        talking_head_clip.close()
        composite_clip.close()
        final_audio.close()
        
        logging.info(f"Successfully combined videos into {output_path}")
        return output_path
        
    except Exception as e:
        logging.error(f"Error combining videos: {str(e)}")
        raise

def create_talking_head_split_screen(temp_dir, script, split_screen_path, output_path, avatar_id=None, voice_id=None):
    """
    Main function to create talking head and combine with B-roll in split screen
    
    Args:
        temp_dir (str): Temporary directory to store files
        script (str): Text script for the talking head
        split_screen_path (str): Path to the existing split screen template or B-roll
        output_path (str): Path for the final output video
        avatar_id (str, optional): Heygen avatar ID to use
        voice_id (str, optional): Voice ID to use for speech
        
    Returns:
        str: Path to the final video
    """
    try:
        # Check if script is too long for Heygen API
        max_script_length = 10000  # Adjust based on Heygen's limits
        if len(script) > max_script_length:
            logging.warning(f"Script length ({len(script)}) exceeds maximum ({max_script_length}). Truncating.")
            script = script[:max_script_length]
        
        # 1. Generate talking head video from Heygen
        talking_head_path = generate_heygen_talking_head(
            script, temp_dir, avatar_id, voice_id
        )
        
        # 2. Combine with the B-roll in split screen layout
        final_video_path = combine_broll_with_talking_head(
            split_screen_path, talking_head_path, output_path, temp_dir
        )
        
        return final_video_path
        
    except Exception as e:
        logging.error(f"Error in create_talking_head_split_screen: {str(e)}")
        raise