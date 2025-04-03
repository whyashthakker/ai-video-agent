from moviepy.editor import (
    AudioFileClip,
    concatenate_audioclips,
    concatenate_videoclips,
    ImageClip,
    VideoClip,
)
import os
import cv2
import numpy as np
import logging

from add_brolls.code import (
    find_matching_category,
    select_random_broll,
    add_broll_to_video,
)


def sliding_effect(image, duration, output_resolution):
    """Apply a left to right sliding effect on the image."""

    # Resize the height while maintaining aspect ratio
    aspect_ratio = image.shape[1] / image.shape[0]
    new_width = int(output_resolution[1] * aspect_ratio)
    resized_image = cv2.resize(image, (new_width, output_resolution[1]))

    # Create an ImageClip from the resized image
    video_clip = ImageClip(np.array(resized_image), duration=duration)

    w, h = video_clip.size
    max_shift = w - output_resolution[0]

    # Define a custom make_frame function for our sliding effect
    def make_frame(t):
        # Calculate the offset dynamically based on the elapsed time and duration
        offset = int(max_shift * t / duration)
        # Extract the relevant section of the image based on the calculated offset
        return video_clip.get_frame(t)[:, offset : offset + output_resolution[0]]

    # Use the custom make_frame function to create a new VideoClip
    sliding_clip = VideoClip(make_frame, duration=duration)
    return sliding_clip


import random


def zoom_in_effect(image, duration, output_resolution):
    """Apply a zoom-in effect on the image."""
    video_clip = ImageClip(np.array(image), duration=duration)

    # Initial and final zoom levels
    start_size = output_resolution
    end_size = (1.5 * output_resolution[0], 1.5 * output_resolution[1])

    def make_frame(t):
        progress = t / duration
        width = int(start_size[0] + progress * (end_size[0] - start_size[0]))
        height = int(start_size[1] + progress * (end_size[1] - start_size[1]))
        frame = video_clip.resize((width, height)).get_frame(t)
        return frame[
            int((height - output_resolution[1]) / 2) : int(
                (height + output_resolution[1]) / 2
            ),
            int((width - output_resolution[0]) / 2) : int(
                (width + output_resolution[0]) / 2
            ),
        ]

    zoomed_clip = VideoClip(make_frame, duration=duration)
    return zoomed_clip


def zoom_out_effect(image, duration, output_resolution):
    """Apply a zoom-out effect on the image."""
    video_clip = ImageClip(np.array(image), duration=duration)

    # Initial and final zoom levels
    start_size = (1.5 * output_resolution[0], 1.5 * output_resolution[1])
    end_size = output_resolution

    def make_frame(t):
        progress = t / duration
        width = int(start_size[0] - progress * (start_size[0] - end_size[0]))
        height = int(start_size[1] - progress * (start_size[1] - end_size[1]))
        frame = video_clip.resize((width, height)).get_frame(t)
        return frame[
            int((height - output_resolution[1]) / 2) : int(
                (height + output_resolution[1]) / 2
            ),
            int((width - output_resolution[0]) / 2) : int(
                (width + output_resolution[0]) / 2
            ),
        ]

    zoomed_clip = VideoClip(make_frame, duration=duration)
    return zoomed_clip


def fade_in_out_effect(image, duration, output_resolution):
    """Apply a modern fade-in and fade-out effect on the image."""
    video_clip = ImageClip(np.array(image), duration=duration).resize(output_resolution)

    fade_duration = 1  # 1 second for both fade in and fade out
    min_opacity = 0.3  # The image will start and end with this opacity level

    def make_frame(t):
        frame = video_clip.get_frame(t)
        if t < fade_duration:
            alpha = min_opacity + (1 - min_opacity) * (t / fade_duration)
            frame = alpha * frame
        elif t > duration - fade_duration:
            alpha = min_opacity + (1 - min_opacity) * ((duration - t) / fade_duration)
            frame = alpha * frame
        return frame

    faded_clip = VideoClip(make_frame, duration=duration)
    return faded_clip


def pan_zoom_effect(image, duration, output_resolution):
    """Apply a pan and zoom effect on the image without black sides."""
    video_clip = ImageClip(np.array(image), duration=duration).resize(output_resolution)

    # Define movement and zoom ranges
    max_pan_shift = output_resolution[0] * 0.1  # Reduced pan shift
    start_zoom = output_resolution
    end_zoom = (
        1.2 * output_resolution[0],
        1.2 * output_resolution[1],
    )  # Increased zoom for a more pronounced effect

    def make_frame(t):
        progress = t / duration
        pan_shift = int(max_pan_shift * progress)
        width = int(start_zoom[0] + progress * (end_zoom[0] - start_zoom[0]))
        height = int(start_zoom[1] + progress * (end_zoom[1] - start_zoom[1]))

        # Adjust the pan_shift to ensure it doesn't go beyond the image boundary
        pan_shift = min(pan_shift, width - output_resolution[0])

        frame = video_clip.resize((width, height)).get_frame(t)
        return frame[:, pan_shift : pan_shift + output_resolution[0]]

    pan_zoom_clip = VideoClip(make_frame, duration=duration)
    return pan_zoom_clip


def heartbeat_effect(image, duration, output_resolution):
    """Apply a heartbeat zoom effect on the image."""
    video_clip = ImageClip(np.array(image), duration=duration).resize(output_resolution)
    max_zoom = 0.1  # Maximum deviation from the original size

    def make_frame(t):
        progress = abs(np.sin(2 * np.pi * t / duration))
        zoom = 1 + max_zoom * progress
        return cv2.resize(
            video_clip.get_frame(t),
            None,
            fx=zoom,
            fy=zoom,
            interpolation=cv2.INTER_LINEAR,
        )

    heartbeat_clip = VideoClip(make_frame, duration=duration)
    return heartbeat_clip


def create_combined_video_audio(
    temp_dir,
    mp3_file_folder,
    video_output_filename,
    image_prompts=[],
    add_brolls=False,
    output_resolution=(1080, 1920),
    fps=24,
):
    mp3_files = sorted(
        [file for file in os.listdir(mp3_file_folder) if file.endswith(".mp3")]
    )
    mp3_files = sorted(mp3_files, key=lambda x: int(x.split("_")[1].split(".")[0]))

    logging.info(f"Detected audio files: {mp3_files}")

    audio_clips = []
    video_clips = []

    effects = [
        sliding_effect,
        zoom_in_effect,
        zoom_out_effect,
        fade_in_out_effect,
        pan_zoom_effect,
        heartbeat_effect,
    ]

    for mp3_file in mp3_files:
        retries = 3
        while retries:
            try:
                audio_clip = AudioFileClip(os.path.join(mp3_file_folder, mp3_file))
                audio_clips.append(audio_clip)

                logging.info(f"Duration of {mp3_file}: {audio_clip.duration} seconds")
                logging.info(f"Processing {mp3_file}")

                image_number = mp3_file.split("_")[1].split(".")[0]
                logging.info(f"Extracted image number: {image_number}")

                img_path = os.path.join(temp_dir, f"{image_number}.jpg")
                logging.info(f"Constructed image path: {img_path}")

                if not os.path.exists(img_path):
                    logging.info(f"Image file {img_path} does not exist!")

                image = cv2.imread(img_path)
                image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

                effect_function = random.choice(effects)

                video_clip = effect_function(
                    image, audio_clip.duration, output_resolution
                )

                if add_brolls and int(image_number) % 2 != 0:
                    try:
                        matched_category = find_matching_category(
                            image_prompts[int(image_number) - 1]
                        )
                        logging.info(f"Matched category: {matched_category}")
                        if matched_category:
                            broll_clip_path = select_random_broll(matched_category)
                            logging.info(f"Selected B-roll: {broll_clip_path}")
                            if broll_clip_path:
                                logging.info("Adding B-roll to video...")
                                video_clip = add_broll_to_video(
                                    video_clip, broll_clip_path
                                )
                                logging.info("Added B-roll to video.")
                    except Exception as e:
                        logging.info(
                            f"Failed to add B-roll due to error: {e}, continuing without B-roll."
                        )

                video_clips.append(video_clip)
                break
            except Exception as e:
                logging.error(
                    f"Failed processing {mp3_file} due to error: {e}. Retrying..."
                )
                retries -= 1

        if retries == 0:
            logging.info(f"Error: Failed to process {mp3_file} after 3 attempts.")

    final_audio = concatenate_audioclips(audio_clips)
    final_video = concatenate_videoclips(video_clips, method="compose")
    final_video = final_video.with_audio(final_audio)
    finalpath = temp_dir + "/" + video_output_filename

    retries = 3

    while retries:
        try:
            final_video.write_videofile(
                finalpath, fps=fps, codec="libx264", audio_codec="aac"
            )
            break
        except Exception as e:
            logging.error(f"Failed to save video due to error: {e}. Retrying...")
            retries -= 1

    if retries == 0:
        logging.info(f"Error: Failed to save video after 3 attempts.")

    return finalpath
