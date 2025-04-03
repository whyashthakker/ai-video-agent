import os
import random
from moviepy.editor import (
    VideoFileClip,
    CompositeVideoClip,
)
from fuzzywuzzy import fuzz
import logging

script_directory = os.path.dirname(__file__)

base_directory = os.path.dirname(script_directory)

video_category_folders = {
    "agriculture_&_gardening": {
        "path": os.path.join(base_directory, "videos", "agriculture_&_gardening"),
        "keywords": {
            "agriculture",
            "gardening",
            "farming",
            "horticulture",
            "plants",
            "cultivation",
            "irrigation",
            "harvesting",
            "planting",
            "landscaping",
            "garden",
            "field",
            "crop",
            "floriculture",
            "greenhouse",
            "watering",
            "soil",
            "fertilizer",
            "seeds",
            "vegetables",
            "fruits",
            "flowers",
        },
    },
    "animals_&_nature": {
        "path": os.path.join(base_directory, "videos", "animals_&_nature"),
        "keywords": {"animals", "nature", "wildlife", "fauna", "flora", "environment"},
    },
    "art_&_culture": {
        "path": os.path.join(base_directory, "videos", "art_&_culture"),
        "keywords": {"art", "culture", "music", "dance", "theatre", "painting"},
    },
    "community": {
        "path": os.path.join(base_directory, "videos", "community"),
        "keywords": {"community", "society", "social", "events", "gathering"},
    },
    "data_analytics": {
        "path": os.path.join(base_directory, "videos", "data_analytics"),
        "keywords": {"data", "analytics", "analysis", "statistics", "information"},
    },
    "digital_communication": {
        "path": os.path.join(base_directory, "videos", "digital_communication"),
        "keywords": {
            "digital",
            "communication",
            "social media",
            "internet",
            "networking",
        },
    },
    "education_&_science": {
        "path": os.path.join(base_directory, "videos", "education_&_science"),
        "keywords": {"education", "science", "learning", "school", "research"},
    },
    "entertainment_&_media": {
        "path": os.path.join(base_directory, "videos", "entertainment_&_media"),
        "keywords": {"entertainment", "media", "movies", "tv", "music"},
    },
    "festivals_&_celebrations": {
        "path": os.path.join(base_directory, "videos", "festivals_&_celebrations"),
        "keywords": {"festivals", "celebrations", "holidays", "events", "parties"},
    },
    "finance_&_economy": {
        "path": os.path.join(base_directory, "videos", "finance_&_economy"),
        "keywords": {"finance", "economy", "money", "business", "market"},
    },
    "food_&_cuisine": {
        "path": os.path.join(base_directory, "videos", "food_&_cuisine"),
        "keywords": {"food", "cuisine", "cooking", "gastronomy", "recipes"},
    },
    "general_interest": {
        "path": os.path.join(base_directory, "videos", "general_interest"),
        "keywords": {"general", "interest", "various", "miscellaneous", "diverse"},
    },
    "health_&_fitness": {
        "path": os.path.join(base_directory, "videos", "health_&_fitness"),
        "keywords": {"health", "fitness", "wellness", "exercise", "nutrition"},
    },
    "law_&_governance": {
        "path": os.path.join(base_directory, "videos", "law_&_governance"),
        "keywords": {"law", "governance", "legal", "government", "regulations"},
    },
    "natural_landscapes": {
        "path": os.path.join(base_directory, "videos", "natural_landscapes"),
        "keywords": {"natural", "landscapes", "outdoors", "scenery", "nature"},
    },
    "real_estate": {
        "path": os.path.join(base_directory, "videos", "real_estate"),
        "keywords": {"real estate", "property", "housing", "architecture", "buildings"},
    },
    "space_exploration": {
        "path": os.path.join(base_directory, "videos", "space_exploration"),
        "keywords": {"space", "exploration", "astronomy", "planets", "cosmos"},
    },
    "sports_&_athletics": {
        "path": os.path.join(base_directory, "videos", "sports_&_athletics"),
        "keywords": {"sports", "athletics", "fitness", "competition", "games"},
    },
    "technology_&_ai": {
        "path": os.path.join(base_directory, "videos", "technology_&_ai"),
        "keywords": {
            "technology",
            "tech",
            "ai",
            "artificial intelligence",
            "innovation",
        },
    },
    "travel_&_geography": {
        "path": os.path.join(base_directory, "videos", "travel_&_geography"),
        "keywords": {"travel", "geography", "tourism", "adventure", "explore"},
    },
    "urban_&_city_life": {
        "path": os.path.join(base_directory, "videos", "urban_&_city_life"),
        "keywords": {"urban", "city", "metropolitan", "modern life", "infrastructure"},
    },
}


def extract_keywords(text):
    try:
        common_words = set(
            ["a", "and", "the", "with", "over", "on", "in", "of", "for", "to"]
        )
        return set(
            word.strip(".,")
            for word in text.lower().split()
            if word not in common_words
        )
    except Exception as e:
        logging.info(f"Error in extracting keywords: {e}")
        return set()


def find_matching_category(prompt, video_category_folders=video_category_folders):
    try:
        prompt_keywords = extract_keywords(prompt)
        max_similarity = 0
        best_match_category = None

        for category, details in video_category_folders.items():
            category_keywords = details["keywords"]
            for keyword in category_keywords:
                for prompt_word in prompt_keywords:
                    similarity = fuzz.ratio(str(prompt_word), str(keyword))
                    if similarity > max_similarity:
                        max_similarity = similarity
                        best_match_category = details["path"]

        if max_similarity > 70:  # Threshold for a match, can be adjusted
            return best_match_category
    except Exception as e:
        logging.info(f"Error in finding matching category: {e}")

    return None


def select_random_broll(category_folder):
    try:
        files = [f for f in os.listdir(category_folder) if f.endswith(".mp4")]
        if files:
            random_file = random.choice(files)
            return os.path.join(category_folder, random_file)
    except FileNotFoundError:
        logging.info(f"Category folder not found: {category_folder}")
    except PermissionError:
        logging.info(f"Permission denied accessing folder: {category_folder}")
    except Exception as e:
        logging.info(f"Error selecting random B-roll: {e}")
    return None


def add_broll_to_video(main_clip, broll_file_path):
    try:
        broll_clip = VideoFileClip(broll_file_path).resize(
            height=500
        )  # Adjust as needed
        x_position = (main_clip.w - broll_clip.w) // 2

        # y_position = ((main_clip.h - broll_clip.h) // 2) + 300

        # posiiton y on bottom

        y_position = (main_clip.h - broll_clip.h) - 300

        broll_clip = broll_clip.with_position((x_position, y_position)).with_duration(
            main_clip.duration
        )

        # y_position = main_clip.h - broll_clip.h - 100  # From the bottom

        # If B-roll duration is longer than main clip, trim it
        # if broll_clip.duration > main_clip.duration:
        #     broll_clip = broll_clip.subclip(0, main_clip.duration)

        # # If B-roll duration is shorter than main clip, add a fade-out effect
        # elif broll_clip.duration < main_clip.duration:
        #     fade_duration = min(2, broll_clip.duration)
        #     broll_clip = broll_clip.fadeout(fade_duration)

        #     # Create a transparent clip to fill the remaining duration
        #     remaining_duration = main_clip.duration - broll_clip.duration
        #     transparent_clip = ColorClip(
        #         size=broll_clip.size, color=(0, 0, 0, 0), duration=remaining_duration
        #     )
        #     broll_clip = concatenate_videoclips([broll_clip, transparent_clip])

        # broll_clip = broll_clip.with_position((x_position, y_position))

        return CompositeVideoClip([main_clip, broll_clip], size=main_clip.size)
    except Exception as e:
        logging.info(f"Error adding B-roll to video: {e}")
    return main_clip
