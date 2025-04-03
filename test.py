from openai import OpenAI

client = OpenAI()

audio_file = open("635edee7-04ac-482d-b0d7-4730e93ef169/combined_video.mp3", "rb")
transcript = client.audio.transcriptions.create(
    file=audio_file,
    model="whisper-1",
    response_format="verbose_json",
    timestamp_granularities=["word"],
)

print(transcript.words)
