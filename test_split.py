import os
import logging
from moviepy.editor import VideoFileClip, ColorClip, CompositeVideoClip, clips_array

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


def create_split_screen_with_placeholder2(
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
            size=(width, bottom_height), color=(0, 0, 0), duration=duration
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


# Test function
def test_split_screen():
    # Define paths
    input_video = "testsplit/combined_video.mp4"  # Replace with actual path
    output_dir = "testsplit/output/"  # Replace with actual path
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    # Define output path
    output_path = os.path.join(output_dir, "split_screen_test.mp4")
    # Run the function
    try:
        result_path = create_split_screen_with_placeholder(
            input_video, output_path, split_ratio=0.5
        )
        logging.info(f"Split screen video created successfully at: {result_path}")
    except Exception as e:
        logging.error(f"Test failed: {str(e)}")


if __name__ == "__main__":
    test_split_screen()
