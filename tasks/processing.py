from celery_config import celery_app
import shutil
import os
import logging


from image_generation.code import (
    generate_images,
    download_and_save_user_images,
    download_and_save_user_audio,
)
from script_generation.code import (
    fetch_imagedescription_and_script,
    generate_prompt,
    chatgpt_url,
    chatgpt_headers,
    clean_prompt,
)
from sound_generation.code import generate_and_save_audio
from sound_generation.background_music import add_background_music
from combine_videos.code import create_combined_video_audio
from split_screen.code import create_split_screen_with_placeholder
from timestamp_extraction.code import (
    extract_audio_from_video,
    transcribe_audio,
    transcribe_audio_with_openai,
    generate_final_video,
)
from transcript_correction.code import phonetic_correction
from communication import *
from s3_operations.code import upload_to_s3, upload_zip_to_s3
from file_operations import zip_directory
from talking_avatar.code import create_talking_head_split_screen

# @celery_app.task(name="shorts_generator", queue="shorts_generator")
def shorts_generator(task_info):
    topic = task_info["topic"]
    goal = task_info["goal"]
    email = task_info["email"]
    userId = task_info["userId"]
    unique_uuid = task_info["unique_uuid"]
    temp_dir = task_info["temp_dir"]
    extra_details = task_info["extra_details"]
    received_voice_id = task_info.get("voice_id")
    brand_name = task_info["brand_name"]
    watermark = task_info["watermark"]
    brand_watermark = task_info["brand_watermark"]
    caption_id = task_info.get("caption_id")
    background_music = task_info.get("background_music")
    background_music_category = task_info.get("background_music_category")
    subtitle_position = task_info.get("subtitle_position")
    text_effect = task_info.get("text_effect")
    add_video = task_info.get("add_video")
    user_images = task_info.get("user_images", [])
    script_language = task_info.get("script_language")
    add_brolls = task_info.get("add_brolls")
    user_mp3s = task_info.get("user_mp3s", [])
    user_script = task_info.get("user_script")
    avatar_id = task_info.get("avatar_id") 

    try:
        video_output_filename = "combined_video.mp4"
        output_video_file = os.path.join(temp_dir, video_output_filename)
        mp3_file_folder = os.path.join(temp_dir, "mp3")

        if user_mp3s is not None and len(user_mp3s) > 0:
            saved_mp3_count = download_and_save_user_audio(user_mp3s, temp_dir)

        if user_images is not None and len(user_images) > 0:
            saved_images_count = download_and_save_user_images(user_images, temp_dir)
        else:
            saved_images_count = 0

        voice_id = received_voice_id if received_voice_id else "alloy"

        try:
            fetch_attempts = 0

            if user_script and user_script.strip():
                prompt = clean_prompt(user_script)
            else:
                prompt = generate_prompt(topic, goal, extra_details, script_language)

            while fetch_attempts < 2:
                (
                    image_prompts,
                    texts,
                    image_category,
                ) = fetch_imagedescription_and_script(
                    prompt, chatgpt_url, chatgpt_headers
                )

                ai_image_prompts = image_prompts[saved_images_count:]

                # Check the length condition
                if len(image_prompts) > 12 or len(texts) > 12:
                    logging.info(
                        f"Length condition not met. Retrying for {unique_uuid}"
                    )
                    fetch_attempts += 1  # Increment the counter for each attempt
                else:
                    break  # Exit the loop if the condition is met

            logging.info("[PROMPTS + IMAGE PROMPTS GENERATED]")

            for i, text in enumerate(texts):
                output_audio_filename = f"audio_{i + 1}"
                generate_and_save_audio(
                    text,
                    temp_dir,
                    output_audio_filename,
                    voice=voice_id,
                )

            logging.info("[SOUND_GENERATED]")

            generate_images(ai_image_prompts, temp_dir, saved_images_count, add_video)

            logging.info("[IMAGES GENERATED.]")

            finalvideoname = create_combined_video_audio(
                temp_dir,
                mp3_file_folder,
                video_output_filename,
                image_category,
                add_brolls,
            )

            logging.info("AUDIO + VIDEO COMBINED")
            
            # Create a combined script with proper spacing between segments
            combined_script = " ".join(texts)
            
            # Path for the talking head video and final output
            talking_head_path = os.path.join(temp_dir, "heygen_talking_head.mp4")
            combined_output_path = os.path.join(temp_dir, "combined_with_talking_head.mp4")
            
            try:
                # Generate the talking head video using Heygen API
                logging.info("Generating talking head video with Heygen API")
                combined_output_path = os.path.join(temp_dir, "combined_with_talking_head.mp4")

                finalvideoname = create_talking_head_split_screen(
                    temp_dir=temp_dir,
                    script=combined_script,
                    split_screen_path=finalvideoname,
                    output_path=combined_output_path,
                    avatar_id=avatar_id,
                    voice_id=voice_id
                )
                
                # Combine the B-roll with the talking head in split screen format
                logging.info("TALKING HEAD VIDEO GENERATED AND COMBINED")
                finalvideoname = combine_broll_with_talking_head(
                    broll_path=finalvideoname,
                    talking_head_path=talking_head_path,
                    output_path=combined_output_path,
                    temp_dir=temp_dir
                )
                
                logging.info("TALKING HEAD VIDEO GENERATED AND COMBINED")
            except Exception as e:
                logging.error(f"Error generating talking head video: {str(e)}")
                # Fall back to placeholder if talking head generation fails
                logging.info("Falling back to placeholder split screen")
                split_screen_path = os.path.join(temp_dir, "split_screen.mp4")
                finalvideoname = create_split_screen_with_placeholder(
                    finalvideoname,
                    split_screen_path,
                    split_ratio=0.5
                )
                
                logging.info("PLACEHOLDER SPLIT SCREEN CREATED")

            if caption_id != "0":
                audiofilename = extract_audio_from_video(temp_dir, output_video_file)

                logging.info("[AUDIO EXTRACTED FROM VIDEO]")

                wordlevel_info = transcribe_audio_with_openai(audiofilename)

                logging.info("[TRANSCRIPTION DONE]")

                if brand_name and brand_name.strip():
                    wordlevel_info = phonetic_correction(
                        wordlevel_info,
                        brand_name,
                        topic,
                        goal,
                        extra_details,
                        user_script,
                    )

                finalvideoname = generate_final_video(
                    wordlevel_info=wordlevel_info,
                    output_video_file=finalvideoname,
                    current_foldername=temp_dir,
                    watermark=watermark,
                    brand_watermark=brand_watermark,
                    text_effect=text_effect,
                    caption_id=caption_id,
                    subtitle_position=subtitle_position,
                )

            if background_music and background_music != "0":
                finalvideoname = add_background_music(
                    finalvideoname, background_music, temp_dir
                )

            logging.info(f"[FINAL VIDEO GENERATED]: {unique_uuid}")

            s3_path = f"{unique_uuid}_final{os.path.splitext(finalvideoname)[1]}"

            try:
                presigned_url = upload_to_s3(finalvideoname, s3_path, userId)
            except Exception as e:
                logging.error(
                    f"Error uploading to S3 for {unique_uuid}. Error: {str(e)}"
                )
                raise

            logging.info(f"[UPLOADED TO S3]: {unique_uuid} {presigned_url}")

            # Notify the user about the successful process via email.
            try:
                send_email(email, presigned_url)
            except Exception as e:
                logging.error(
                    f"Error sending email to {email}. Error: {str(e)} for {unique_uuid}"
                )

            logging.info(f"[EMAIL_SENT] for {unique_uuid}")

            # Trigger the webhook on successful processing.
            try:
                trigger_webhook(unique_uuid, presigned_url, output_video_file)
            except Exception as e:
                logging.error(
                    f"Error triggering webhook for {unique_uuid}. Error: {str(e)}"
                )

            logging.info(f"WEBHOOK_TRIGGERED for {unique_uuid}")

        except Exception as e:
            logging.error(f"[SOMETHING WENT WRONG]. {unique_uuid} Error: {str(e)}")
            try:
                send_failure_webhook(str(e), unique_uuid)
            except Exception as e:
                logging.error(
                    f"Error triggering webhook for {unique_uuid}. Error: {str(e)}"
                )

    finally:
        try:
            if os.path.exists(temp_dir):
                # Step 1: Zip the directory
                zip_path = os.path.join(temp_dir, f"{temp_dir}.zip")
                zip_directory(temp_dir, zip_path)
                
                # You can uncomment the below if you want to upload and clean up
                # # Step 2: Upload to S3
                # unique_s3_path = f"{unique_uuid}.zip"
                # try:
                #     upload_zip_to_s3(zip_path, unique_s3_path, userId="system")
                #     logging.info(f"[UPLOADED ZIP TO S3]: {unique_uuid}")
                # except Exception as e:
                #     logging.error(
                #         f"Error uploading to S3 for {unique_uuid}. Error: {str(e)}"
                #     )
                # # Step 3: Remove the temporary directory
                # shutil.rmtree(temp_dir)
                # logging.info(f"[CLEANED FILES]: {unique_uuid}")

        except Exception as e:
            logging.error(f"Error cleaning up files for {unique_uuid}. Error: {str(e)}")