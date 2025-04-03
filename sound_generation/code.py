from dotenv import load_dotenv
import os
import requests
import logging
from openai import OpenAI
from elevenlabs.client import ElevenLabs
from elevenlabs import Voice, VoiceSettings, save

load_dotenv()

openai_api_key = os.environ.get("OPENAI_API_KEY")
elevenlabs_api_key = os.environ.get("ELEVENLABS_API_KEY")


def generate_and_save_audio(
    text,
    temp_dir,
    filename,
    voice="alloy",
    model="tts-1",
    output_format="mp3",
    stability=0.4,
    similarity_boost=0.80,
):
    file_path = os.path.join(temp_dir, output_format, f"{filename}.{output_format}")

    if os.path.exists(file_path):
        logging.info(f"Audio file {file_path} already exists. Reusing.")
        return file_path

    if voice in ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]:
        # Use OpenAI voice generation
        openai_client = OpenAI(api_key=openai_api_key)

        logging.info(f"Generating audio for '{text}' using OpenAI")

        retries = 3
        while retries:
            try:
                response = openai_client.audio.speech.create(
                    model=model,
                    voice=voice,
                    input=text,
                )

                if not os.path.exists(f"{temp_dir}/mp3"):
                    os.makedirs(f"{temp_dir}/mp3")

                response.stream_to_file(file_path)

                break
            except Exception as e:
                logging.error(
                    f"Failed to generate audio using OpenAI: {e}. Retrying..."
                )
                retries -= 1

        if retries == 0:
            logging.error("Failed to generate audio after 3 attempts using OpenAI.")
    else:
        # Use ElevenLabs voice generation
        client = ElevenLabs(api_key=elevenlabs_api_key)

        logging.info(f"Generating audio for '{text}' using ElevenLabs")

        retries = 3
        while retries:
            try:
                audio = client.generate(
                    text=text,
                    voice=Voice(
                        voice_id=voice,
                        settings=VoiceSettings(
                            stability=stability, similarity_boost=similarity_boost
                        ),
                    ),
                    model="eleven_multilingual_v2",
                )

                if not os.path.exists(f"{temp_dir}/mp3"):
                    os.makedirs(f"{temp_dir}/mp3")

                save(audio, file_path)

                # with open(file_path, "wb") as f:
                #     f.write(audio)

                break
            except Exception as e:
                logging.error(
                    f"Failed to generate audio using ElevenLabs: {e}. Retrying..."
                )
                retries -= 1

        if retries == 0:
            logging.error("Failed to generate audio after 3 attempts using ElevenLabs.")

    return file_path
