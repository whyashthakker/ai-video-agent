from fastapi import FastAPI, HTTPException, Header, Depends
from pydantic import BaseModel
from dotenv import load_dotenv
from typing import Optional
import os
import logging
from uuid import uuid4

from tasks.processing import shorts_generator

from communication import send_failure_webhook

load_dotenv()

app = FastAPI()


class ShortsProcessingItem(BaseModel):
    topic: str
    goal: str
    email: str
    userId: str
    extra_details: str
    voice_id: Optional[str] = None
    brand_name: Optional[str] = None
    watermark: bool = True
    brand_watermark: Optional[str] = None
    caption_id: Optional[str] = None
    background_music: Optional[str] = None
    background_music_category: Optional[str] = None
    subtitle_position: Optional[str] = None
    text_effect: Optional[str] = None
    add_video: Optional[bool] = False
    user_images: Optional[list] = None
    script_language: Optional[str] = None
    add_brolls: Optional[bool] = False
    user_mp3s: Optional[list] = None
    user_script: Optional[str] = None


def verify_authorization_key(authorization_key: str = Header(...)):
    CONFIGURED_KEYS = os.environ.get("AUTH_KEY")
    if authorization_key not in CONFIGURED_KEYS:
        raise HTTPException(status_code=403, detail="Not authorized")
    return authorization_key


@app.post("/generate-shorts/")
async def process_short(
    item: ShortsProcessingItem, authorization: str = Depends(verify_authorization_key)
):
    # Extracting parameters from the request payload
    topic = item.topic
    goal = item.goal
    email = item.email
    userId = item.userId
    extra_details = item.extra_details
    voice_id = item.voice_id
    brand_name = item.brand_name
    watermark = item.watermark
    brand_watermark = item.brand_watermark
    caption_id = item.caption_id
    background_music = item.background_music
    background_music_category = item.background_music_category
    subtitle_position = item.subtitle_position
    text_effect = item.text_effect
    add_video = item.add_video
    user_images = item.user_images
    script_language = item.script_language
    add_brolls = item.add_brolls
    user_mp3s = item.user_mp3s
    user_script = item.user_script

    unique_uuid = str(uuid4())

    temp_dir = unique_uuid
    # temp_dir = (
    #     "/Users/yash/code/ai-generated-shorts/635edee7-04ac-482d-b0d7-4730e93ef169"
    # )

    task_info = {
        "topic": topic,
        "goal": goal,
        "extra_details": extra_details,
        "email": email,
        "userId": userId,
        "unique_uuid": unique_uuid,
        "temp_dir": temp_dir,
        "voice_id": voice_id,
        "brand_name": brand_name,
        "watermark": watermark,
        "brand_watermark": brand_watermark,
        "caption_id": caption_id,
        "background_music": background_music,
        "background_music_category": background_music_category,
        "subtitle_position": subtitle_position,
        "text_effect": text_effect,
        "add_video": add_video,
        "user_images": user_images,
        "script_language": script_language,
        "add_brolls": add_brolls,
        "user_mp3s": user_mp3s,
        "user_script": user_script,
    }

    # Check for restricted brand watermark or brand name
    if item.brand_watermark == "MANO TECH IRHA" or item.brand_name == "MANO TECH IRHA":
        error_message = "We have a downtime, please try again in some time."
        send_failure_webhook(error_message, unique_uuid)
        raise HTTPException(status_code=400, detail=error_message)

    logging.info(f"Starting video processing for {unique_uuid}")

    # shorts_generator.apply_async((task_info,))

    shorts_generator(task_info)

    logging.info(f"Video processing started for {unique_uuid}")

    return {
        "status": "Video processing started. You will be notified by email once it's done.",
        "request_id": unique_uuid,
    }
