import subprocess
import requests
import os
from sound_generation.background_audio_files import background_music
import logging


def get_video_duration(video_path):
    """Get the duration of the video in seconds."""
    cmd = [
        "ffprobe",
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "default=noprint_wrappers=1:nokey=1",
        video_path,
    ]
    return float(subprocess.check_output(cmd).decode("utf-8").strip())


def add_background_music(video_name, audio_id, output_dir="."):
    video_duration = get_video_duration(video_name)

    # start_time, end_time = select_audio_section("temp_audio.mp3", video_duration)

    temp_audio_path = os.path.join(output_dir, "temp_music.mp3")

    output_video_name = os.path.join(
        output_dir, "with_bg_music_" + os.path.basename(video_name)
    )

    # Get the audio URL based on the given ID
    background_music_url = background_music.get(audio_id, {}).get("url")
    if not background_music_url:
        raise ValueError(f"No background audio found for ID '{audio_id}'.")

    audio_data = requests.get(background_music_url).content
    with open(temp_audio_path, "wb") as audio_file:
        audio_file.write(audio_data)

    # The filter to trim the audio, add fade out, and mix with the video's original audio
    filter_complex = f"[1:a]volume=0.05,atrim=duration={video_duration},afade=t=out:st={video_duration-2}:d=2[a1];[0:a][a1]amix=inputs=2:duration=first[aout]"

    cmd = [
        "ffmpeg",
        "-i",
        video_name,
        "-i",
        temp_audio_path,
        "-filter_complex",
        filter_complex,
        "-map",
        "0:v",
        "-map",
        "[aout]",
        "-c:v",
        "copy",
        "-c:a",
        "aac",
        output_video_name,
    ]

    # Execute the command
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        logging.info("Command failed with return code:", result.returncode)
        logging.info("Standard Output:", result.stdout)
        logging.info("Error Output:", result.stderr)
        raise subprocess.CalledProcessError(result.returncode, cmd)

    return output_video_name
