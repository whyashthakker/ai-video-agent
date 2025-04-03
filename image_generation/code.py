import os
from PIL import Image, ImageFilter

# import ipyplot
import os
import io
import requests
from PIL import Image
import random
from dotenv import load_dotenv
import logging
import replicate

from pydub import AudioSegment

from openai import OpenAI

openai_api_key = os.environ.get("OPENAI_API_KEY")

client = OpenAI(api_key=openai_api_key)

# from generate_video.code import generate_video

load_dotenv()

segmind_apikey = os.environ.get("SEGMIND_APIKEY")

segmind_model_name = os.environ.get("SEGMIND_MODEL_NAME")


def resize_image_to_square(image, size=(1024, 1024), min_size=(200, 200)):
    # Check if the image is too small
    if image.width < min_size[0] or image.height < min_size[1]:
        return None

    # Compute the new size
    aspect_ratio = image.width / image.height
    if aspect_ratio > 1:  # Width is greater than height
        new_width = size[0]
        new_height = round(new_width / aspect_ratio)
    else:  # Height is greater or equal to width
        new_height = size[1]
        new_width = round(new_height * aspect_ratio)

    # Resize the image
    resized_image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)

    # Check if the resized image is smaller than the target size
    if resized_image.width < size[0] or resized_image.height < size[1]:
        # Create a blurred background
        blurred_background = resized_image.copy().resize(size, Image.Resampling.LANCZOS)
        blurred_background = blurred_background.filter(
            ImageFilter.GaussianBlur(radius=15)
        )

        # Ensure both images are in RGB mode
        resized_image = resized_image.convert("RGB")
        blurred_background = blurred_background.convert("RGB")

        # Now, paste the resized image onto the blurred background
        blurred_background.paste(
            resized_image, ((size[0] - new_width) // 2, (size[1] - new_height) // 2)
        )
        return blurred_background
    else:
        return resized_image


def download_and_save_user_audio(mp3_links, temp_dir):
    os.makedirs(os.path.join(temp_dir, "mp3"), exist_ok=True)

    saved_mp3_count = 0
    for i, link in enumerate(mp3_links):
        try:
            response = requests.get(link)
            if response.status_code == 200:
                saved_mp3_count += 1
                mp3_filename = os.path.join(
                    temp_dir, "mp3", f"audio_{saved_mp3_count}.mp3"
                )
                with open(mp3_filename, "wb") as mp3_file:
                    mp3_file.write(response.content)

                # Crop the audio to 5 seconds
                audio = AudioSegment.from_mp3(mp3_filename)
                cropped_audio = audio[:5000]  # Crop to first 5 seconds
                cropped_audio.export(
                    mp3_filename, format="mp3"
                )  # Overwrite original file

                logging.info(f"User audio {saved_mp3_count} saved as '{mp3_filename}'")
            else:
                logging.info(f"Failed to download user audio {i + 1}")
        except Exception as e:
            logging.error(f"Error while processing audio {i + 1}: {e}")

    return saved_mp3_count


def download_and_save_user_images(image_links, temp_dir):
    os.makedirs(temp_dir, exist_ok=True)

    saved_images_count = 0
    for i, link in enumerate(image_links):
        try:
            response = requests.get(link)
            if response.status_code == 200:
                image_data = response.content
                with Image.open(io.BytesIO(image_data)) as img:
                    resized_image = resize_image_to_square(img)
                    if resized_image is not None:
                        saved_images_count += 1
                        image_filename = os.path.join(
                            temp_dir, f"{saved_images_count}.jpg"
                        )
                        resized_image.save(image_filename, format="JPEG")
                        logging.info(
                            f"User image {saved_images_count} saved as '{image_filename}'"
                        )
                    else:
                        logging.info(
                            f"Image {i + 1} is too small for processing and was skipped."
                        )
            else:
                logging.info(f"Failed to download user image {i + 1}")
        except Exception as e:
            logging.error(f"Error while processing image {i + 1}: {e}")

    return saved_images_count


def generate_images(prompts, temp_dir, start_index, add_video=False):
    logging.info(f"Generating {len(prompts)} images")

    # Common Setup
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)

    if add_video:
        # Generate video for the first prompt
        # generate_video(prompts[0], temp_dir)
        prompts = prompts[1:]  # Remove the first prompt
        add_video = False  # Reset the flag to generate images for the remaining prompts

    num_images = len(prompts)
    currentseed = random.randint(1, 1000000)

    # Segmind API setup
    segmind_url = "https://api.segmind.com/v1/ssd-1b"
    segmind_headers = {"x-api-key": segmind_apikey}

    # Replicate API setup
    replicate_model_id = "stability-ai/sdxl:8beff3369e81422112d93b89ca01426147de542cd4684c244b673b105188fe5f"

    for i, prompt in enumerate(prompts, start=start_index):
        image_filename = os.path.join(temp_dir, f"{i + 1}.jpg")
        if os.path.exists(image_filename) and i < 11:
            logging.info(f"Image {i + 1} already exists. Skipping...")
            continue

        if (i - 1) % 3 == 0:  # Use DALL-E 3 for every 3rd image
            try:
                response = client.images.generate(
                    prompt=prompt,
                    n=1,
                    size="1024x1024",
                    model="dall-e-3",  # Generate one image at a time
                )
                image_url = response.data[0].url  # Get the URL of the generated image

                # Download the image from the URL
                image_response = requests.get(image_url)
                if image_response.status_code == 200:
                    with open(image_filename, "wb") as f:
                        f.write(image_response.content)
                    logging.info(f"DALL-E generated image saved as '{image_filename}'")
                    continue  # Skip to next prompt if successful
                else:
                    raise Exception(f"Failed to download image from URL: {image_url}")
            except Exception as e:
                logging.error(f"Error in DALL-E image generation: {e}")

        # Segmind API call
        try:
            final_prompt = "{}, closeup, enhance, ((perfect quality)), ((ultrahd)), ((realistic)), ((cinematic photo:1.3)), ((raw candid)), 4k, no occlusion, Fujifilm XT3, highly detailed, bokeh, cinemascope".format(
                prompt.strip(".")
            )
            negative_prompt = "((deformed)), ((limbs cut off)), ((quotes)), ((extra fingers)), ((deformed hands)), extra limbs, disfigured, blurry, bad anatomy, absent limbs, blurred, watermark, disproportionate, grainy, signature, cut off, missing legs, missing arms, poorly drawn face, bad face, fused face, cloned face, worst face, three crus, extra crus, fused crus, worst feet, three feet, fused feet, fused thigh, three thigh, fused thigh, extra thigh, worst thigh, missing fingers, extra fingers, ugly fingers, long fingers, horn, extra eyes, amputation, disconnected limbs "  # truncated for brevity
            segmind_data = {
                "prompt": final_prompt,
                "negative_prompt": negative_prompt,
                "style": "enhance",
                "samples": 1,
                "scheduler": "UniPC",
                "num_inference_steps": 40,
                "guidance_scale": 8,
                "strength": 1,
                "seed": currentseed,
                "img_width": 1024,
                "img_height": 1024,
                "refiner": "yes",
                "base64": False,
            }

            response = requests.post(
                segmind_url, json=segmind_data, headers=segmind_headers
            )

            if (
                response.status_code == 200
                and response.headers.get("content-type") == "image/jpeg"
            ):
                image_data = response.content
                image = Image.open(io.BytesIO(image_data))
                image.save(image_filename)
                logging.info(f"Image {i + 1}/{num_images} saved as '{image_filename}'")
                continue

        except Exception:
            # If there's an error, we fallback to the replicate API
            pass

        # Replicate API call (fallback)
        try:
            replicate_parameters = {
                "prompt": final_prompt,
                "negative_prompt": negative_prompt,
                "width": 1024,
                "height": 1024,
                "scheduler": "K_EULER",
                "num_inference_steps": 40,
                "guidance_scale": 7.5,
                "prompt_strength": 0.8,
                "seed": currentseed,
                "refine": "base_image_refiner",
            }
            output = replicate.run(replicate_model_id, input=replicate_parameters)
            image_url = output[0]  # Assuming the model returns a single URL per prompt
            response = requests.get(image_url)
            image_data = response.content
            image = Image.open(io.BytesIO(image_data))
            image.save(image_filename)
            logging.info(
                f"AI-generated image {i + 1}/{len(prompts) + start_index} saved as '{image_filename}'"
            )

        except Exception as e:
            logging.info(f"Failed to retrieve or save image {i + 1} due to error: {e}")
