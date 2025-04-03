from dotenv import load_dotenv
import os
import requests
import logging

load_dotenv()

elevenlabsapi = os.environ.get("ELEVENLABS_API_KEY")


def generate_and_save_audio(
    text,
    temp_dir,  # <-- Add temp_dir as an argument
    filename,
    voice_id,
    elevenlabs_apikey,
    model_id="eleven_multilingual_v2",
    stability=0.4,
    similarity_boost=0.80,
):
    file_path = os.path.join(temp_dir, "mp3", f"{filename}.mp3")

    if os.path.exists(file_path):
        logging.info(f"Audio file {file_path} already exists. Reusing.")
        return file_path

    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    headers = {
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
        "xi-api-key": elevenlabs_apikey,
    }

    data = {
        "text": text,
        "model_id": model_id,
        "voice_settings": {
            "stability": stability,
            "similarity_boost": similarity_boost,
        },
    }

    logging.info(f"Generating audio for '{text}'")

    retries = 3
    while retries:
        try:
            response = requests.post(url, json=data, headers=headers)

            if response.status_code != 200:
                logging.error(
                    f"API returned status code {response.status_code}. Retrying..."
                )
                retries -= 1
                continue
            else:
                if not os.path.exists(f"{temp_dir}/mp3"):
                    os.makedirs(f"{temp_dir}/mp3")
                file_path = f"{temp_dir}/mp3/{filename}.mp3"
                with open(file_path, "wb") as f:
                    f.write(response.content)
                break
        except Exception as e:
            logging.error(f"Failed due to error: {e}. Retrying...")
            retries -= 1

    if retries == 0:
        logging.error(f"Failed to generate audio after 3 attempts.")
