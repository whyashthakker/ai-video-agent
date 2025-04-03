import requests
import json
import os
from dotenv import load_dotenv
import logging

load_dotenv()

openaikey = os.environ.get("OPENAI_API_KEY")

chatgpt_url = "https://api.openai.com/v1/chat/completions"

chatgpt_headers = {
    "content-type": "application/json",
    "Authorization": "Bearer {}".format(openaikey),
}

logging.basicConfig(
    level=logging.INFO, format="[WRITING_SHORTS_SCRIPT] %(asctime)s - %(message)s"
)


def fetch_imagedescription_and_script(prompt, url, headers):
    retries = 10
    while retries:
        try:
            logging.info("[FETCHING_IMAGE_DESCRIPTION_AND_SCRIPT]")

            messages = [
                {
                    "role": "system",
                    "content": "You are an expert short video script writer and story teller for short form videos with expertise in Ads, educational content, AI Generated Stories, and General Short Video Content for Instagram Reels, YouTube Shorts and Tiktok. Your Goal is to create viral short videos.",
                },
                {"role": "user", "content": prompt},
            ]

            chatgpt_payload = {
                "model": "gpt-3.5-turbo-16k",
                # "model": "gpt-4-1106-preview",
                "messages": messages,
                "temperature": 1.3,
                "max_tokens": 3500,
                "top_p": 1,
                "stop": ["###"],
            }

            response = requests.post(url, json=chatgpt_payload, headers=headers)
            response_json = response.json()

            output = json.loads(
                response_json["choices"][0]["message"]["content"].strip()
            )

            logging.info(f"[PROMPT_OUTPUT_GENERATED]")

            image_prompts = [k["image_description"] for k in output]
            texts = [k["text"] for k in output]
            image_category = [k["image_category"] for k in output]

            return image_prompts, texts, image_category
        except Exception as e:
            logging.error(f"Failed due to error: {e}. Retrying...")
            retries -= 1

    raise Exception("Failed after 3 attempts.")


def clean_prompt(user_script):
    logging.info("[CLEANING SCRIPT]")

    prompt_prefix = f"""You are a viral content creator focused on producing engaging and shareable content. Your task is to refine the script shared by the user without changing the content of the script.

        Please follow these instructions to create an engaging and impactful short video:
        1. Breakdown the script into logical 8-10 scenes maximum and 6 minumum. Transition smoothly between scenes, changing every 5-7 seconds to maintain engagement. If you think the script if falling short of scenes, feel free to generate some scenes yourself.
        2. For each scene cut, provide a detailed description of the stock image being shown.
        3. Show the user script text with each image description that we can generate. 
        4. Sequence your scenes in a way that builds anticipation, making viewers eager to share.
        5. There must always be a conclusion in the last scene. The conclusion should be a call to action that encourages viewers to think about a question it must be a generic question. Example: What do you think about this, make it relevant to context. There must always only be a single Call to Action.
        6. Ensure user script is in a logical format. Example: If you are talking about a topic, you must start with a question, then provide a description, then provide a text that complements the description, then provide a conclusion with a call to action.
        7. The image_description and text must be relevant to the topic and at least 15 words capturing all the details to generate in an image. So ensure you pass one word knowledge about the topic in image_description to retain context. Example, if it's about Black holes, then you should include the word "Space, Sci-fi, Educational" in the image_description. If it's about cats, image description must include the cat. Think about it as alt text but a little more detailed covering all important bits.
        8. Strictly output your response in a JSON list format, adhering to the following sample structure:"""

    sample_output = """
    [
        { "image_description": "Image Description of the first scene here.", "image_category": "technology", "text": "User shared script - 1" },
        { "image_description": "Image Description of the second scene here", "image_category": "nature", "text": "User shared script - 2" },
        ...
    ] """

    prompt_postinstruction = f"""While our most preferred image_descriptions is 6. Your script must not exceed 9 image_descriptions in any scenario. Here's the user script: {user_script}
    Output:"""

    prompt = prompt_prefix + sample_output + prompt_postinstruction

    return prompt


def generate_prompt(topic, goal, extra_details="", script_language="English"):
    logging.info("[GENERATING_PROMPT]")

    extra_details_phrase = (
        f", some extra details {extra_details} for your reference"
        if extra_details
        else ""
    )

    script_language_phrase = (
        f" Text should be in {script_language} and image_description in English."
        if script_language != "English"
        else ""
    )

    prompt_prefix = f"""You are a viral content creator focused on producing engaging and shareable content. Your task is to create a script for the topic: {topic}. The video should be around 45 seconds, capturing the essence of the topic and evoking emotion to make it highly shareable.
    Our primary goal is to {goal}{extra_details_phrase}, {script_language_phrase}
    Please follow these instructions to create an engaging and impactful short video:
    1. Start with a scene that immediately grabs the viewer's attention and evokes curiosity. Always start with a question.
    2. Transition smoothly between scenes, changing every 5-7 seconds to maintain engagement.
    3. For each scene cut, provide a detailed description of the stock image being shown. But avoid repeition at all costs.
    4. Along with each image description, include a corresponding text that complements and enhances the visual. The text should be concise and powerful.
    5. Sequence your scenes in a way that builds anticipation, making viewers eager to share.
    6. People only share content that makes them look smart. Avoid Emojis and Hashtags at all Cost.
    7. There must always be a conclusion in the last scene. The conclusion should be a call to action that encourages viewers to think about a question it must be a generic question. Example: What do you think about this? There must always only be a single Call to Action.
    8. All your texts must be in a logical format. Example: If you are talking about a topic, you must start with a question, then provide a description, then provide a text that complements the description, then provide a conclusion with a call to action.
    9. The image_description and text must be relevant to the topic and at least 15 words capturing all the details to generate in an image. So ensure you pass one word knowledge about the topic in image_description to retain context. Example, if it's about Black holes, then you should include the word "Space, Sci-fi, Educational" in the image_description. If it's about cats, image description must include the cat. Think about it as alt text but a little more detailed covering all important bits.
    10. Strictly output your response in a JSON list format, adhering to the following sample structure:"""

    sample_output = """
    [
        { "image_description": "Description of the first image here.", "image_category": "technology", "text": "Text accompanying the first scene cut." },
        { "image_description": "Description of the second image here.", "image_category": "nature", "text": "Text accompanying the second scene cut." },
        ...
    ] """

    prompt_postinstruction = f"""While our most preferred image_descriptions is 6. Your script must not exceed 9 image_descriptions in any scenario.
    Output:"""

    prompt = prompt_prefix + sample_output + prompt_postinstruction

    return prompt
