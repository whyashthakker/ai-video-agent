import os
import io
import requests
from PIL import Image
import random
import replicate
import logging


def generate_video(prompt, temp_dir):
    # Ensure the directory exists
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)

    # Set a random seed for the generation
    currentseed = random.randint(1, 1000000)

    # Replicate API setup
    replicate_model_id = "lucataco/hotshot-xl:b57dddff6ae2029be57eab3d17e0de5f1c83b822f0defd8ce49bee44d7b52ee6"
    image_filename = os.path.join(
        temp_dir, "output.mp4" if prompt.get("mp4", False) else "output.jpg"
    )

    # Format the prompt and negative prompt
    final_prompt = "{}, closeup, enhance, ((perfect quality)), ((ultrahd)), ((realistic)), ((cinematic photo:1.3)), ((raw candid)), 4k, no occlusion, Fujifilm XT3, highly detailed, bokeh, cinemascope".format(
        prompt.strip(".")
    )
    negative_prompt = "((deformed)), ((limbs cut off)), ((quotes)), ((extra fingers)), ((deformed hands)), extra limbs, disfigured, blurry, bad anatomy, absent limbs, blurred, watermark, disproportionate, grainy, signature, cut off, missing legs, missing arms, poorly drawn face, bad face, fused face, cloned face, worst face, three crus, extra crus, fused crus, worst feet, three feet, fused feet, fused thigh, three thigh, fused thigh, extra thigh, worst thigh, missing fingers, extra fingers, ugly fingers, long fingers, horn, extra eyes, amputation, disconnected limbs "  # truncated for brevity

    try:
        # Build the parameters
        replicate_parameters = {
            "prompt": final_prompt,
            "negative_prompt": negative_prompt,
            "scheduler": prompt.get("scheduler", "EulerAncestralDiscreteScheduler"),
            "steps": prompt.get("steps", 30),
            "mp4": prompt.get("mp4", False),
            "seed": currentseed,
        }
        output = replicate.run(replicate_model_id, input=replicate_parameters)

        # If the output is a URL, download the content
        if isinstance(output, str) and output.startswith("http"):
            response = requests.get(output)
            with open(image_filename, "wb") as f:
                f.write(response.content)
        else:
            # If the output is directly the image data
            image_data = output.content
            image = Image.open(io.BytesIO(image_data))
            image.save(image_filename)

        logging.info(f"Video saved as '{image_filename}'")

    except Exception as e:
        logging.info(f"Failed to retrieve or save image due to error: {e}")
