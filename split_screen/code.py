import logging
from moviepy.editor import VideoFileClip, ColorClip, clips_array


def create_split_screen_with_placeholder(
    broll_video_path, output_path, split_ratio=0.5
):
    """
    Creates a split-screen video with a black placeholder at the bottom (for future user/avatar)
    and B-roll video at the top.
    Args:
        broll_video_path: Path to the B-roll video (will be placed at top)
        output_path: Path where the final split-screen video will be saved
        split_ratio: Vertical position for the split (0.5 means equal halves)
    Returns:
        Path to the generated split-screen video
    """

    try:
        # Get video dimensions and duration for the B-roll
        broll_video = VideoFileClip(broll_video_path)
        duration = broll_video.duration
        # Get the audio from the original video
        original_audio = broll_video.audio
        # Target dimensions (from your defaults)
        width, height = 1080, 1920
        top_height = int(height * split_ratio)
        bottom_height = height - top_height
        # Resize the B-roll video to fit the top section
        broll_resized = broll_video.resize(width=width, height=top_height)
        # Create a black clip for the bottom section (placeholder for future user/avatar)
        # Remove .set_duration() and only use the duration parameter
        placeholder_clip = ColorClip(
            size=(width, bottom_height), color=(255, 0, 0), duration=duration
        )
        # Create the composition with clips array
        combined_clip = clips_array([[broll_resized], [placeholder_clip]])
        # Set the audio
        if original_audio is not None:
            combined_clip = combined_clip.with_audio(original_audio)
        # Write the final video
        combined_clip.write_videofile(
            output_path,
            codec="libx264",
            audio_codec="aac" if original_audio is not None else None,
        )
        # Clean up
        broll_video.close()
        return output_path
    except Exception as e:
        logging.error(f"Failed to create split-screen video: {str(e)}")
        raise e  # Re-raise to see full stack trace when testing
