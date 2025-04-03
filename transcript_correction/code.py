import re
from metaphone import doublemetaphone
import logging
import nltk

nltk.download("words")

from nltk.corpus import words


def is_common_word(word):
    return word.lower() in words.words()


def to_phonetic(word):
    phonetic_representation, _ = doublemetaphone(word)
    return phonetic_representation


def phonetic_correction(
    wordlevel_info, brand_name, topic, goal, extra_details, user_script
):
    # reference_paragraph = " ".join(
    #     [brand_name, topic, goal, extra_details, user_script]
    # )

    # just pass brand name

    reference_paragraph = " ".join([brand_name])

    # reference_paragraph = re.sub(r"[^a-zA-Z0-9\s]", "", reference_paragraph)

    # Split the reference paragraph using regex to handle combined words, numbers, and punctuations
    reference_words = re.findall(r"[\w]+|[,.;!?]", reference_paragraph)

    # Convert words to their phonetic forms
    phonetics_reference = {to_phonetic(word): word for word in reference_words}

    for entry in wordlevel_info:
        original_word = entry["word"]

        if is_common_word(original_word):
            continue

        if "." in original_word:
            corrected_word_parts = []
            for part in original_word.split("."):
                part_phonetic = to_phonetic(part)
                if part_phonetic in phonetics_reference:
                    corrected_word_parts.append(phonetics_reference[part_phonetic])
                else:
                    corrected_word_parts.append(part)
            original_word = ".".join(corrected_word_parts)
        else:
            word_phonetic = to_phonetic(original_word)
            if (
                word_phonetic in phonetics_reference
                and original_word.lower() != phonetics_reference[word_phonetic].lower()
            ):
                logging.info(
                    f"Correcting {entry['word']} to {phonetics_reference[word_phonetic]}"
                )
                original_word = phonetics_reference[word_phonetic]

    return wordlevel_info
