# Shorts Generator

An automated video generation system that creates short-form videos from user inputs. This service can generate videos with AI-generated content or utilize user-provided assets.

## Overview

The Shorts Generator is a comprehensive pipeline that:
- Generates scripts based on topics and goals
- Creates images using AI or user-provided assets
- Converts text to speech with customizable voices
- Combines media into short-form videos
- Adds captions, watermarks, and effects
- Delivers the final product via email and webhooks

## Prerequisites

- Docker and Docker Compose
- Access to required APIs (ChatGPT, text-to-speech, etc.)
- S3-compatible storage bucket

## Environment Setup

1. Clone this repository:
   ```bash
   git clone https://github.com/yourusername/shorts-generator.git
   cd shorts-generator
   ```

2. Create a `.env` file in the project root with the following variables:

   ```
   # API Keys
   OPENAI_API_KEY=your_openai_api_key
   ELEVENLABS_API_KEY=your_elevenlabs_api_key

   # AWS Configuration
   AWS_ACCESS_KEY_ID=your_aws_access_key_id
   AWS_SECRET_ACCESS_KEY=your_aws_secret_access_key
   AWS_S3_BUCKET_NAME=your_s3_bucket_name
   AWS_REGION=us-east-1

   # Email Settings
   SMTP_HOST=smtp.youremailprovider.com
   SMTP_PORT=587
   SMTP_USERNAME=your_smtp_username
   SMTP_PASSWORD=your_smtp_password
   EMAIL_FROM=noreply@yourdomain.com

   # Webhook Configuration
   WEBHOOK_URL=https://yourdomain.com/api/webhook
   
   # Application Settings
   TEMP_FILES_PATH=/tmp/shorts-generator
   LOG_LEVEL=INFO
   
   # Optional Integrations
   BACKGROUND_MUSIC_FOLDER=/app/assets/background_music
   BROLL_FOOTAGE_FOLDER=/app/assets/broll
   ```

3. Adjust the values according to your specific setup.

## Building and Running with Docker Compose

1. Build the Docker containers:
   ```bash
   docker-compose build
   ```

2. Start the services:
   ```bash
   docker-compose up
   ```

   Or run in detached mode:
   ```bash
   docker-compose up -d
   ```

3. To view logs when running in detached mode:
   ```bash
   docker-compose logs -f
   ```

4. To stop the services:
   ```bash
   docker-compose down
   ```

## API Usage

The service can be triggered by sending a POST request to the API endpoint:

```bash
curl -X POST http://0.0.0.0:8001/generate-shorts/ \
  -H "Content-Type: application/json" \
  -H "authorization-key: 13131" \
  -d '{
    "topic": "Sustainable living tips",
    "goal": "Educate viewers on easy sustainable practices",
    "email": "aryan@explainx.ai",
    "userId": "user_identifier",
    "extra_details": "Focus on low-cost, high-impact sustainable living practices",
    "voice_id": "alloy",
    "brand_name": "EcoFriendly",
    "watermark": true,
    "brand_watermark": "EcoFriendly Logo",
    "caption_id": "1",
    "background_music": "relaxed",
    "background_music_category": "acoustic",
    "subtitle_position": "bottom", 
    "text_effect": "fade",
    "add_video": false,
    "script_language": "en",
    "add_brolls": true,
    "user_script": "Today we\'re exploring five simple ways to reduce your carbon footprint..."
  }'
```

The API requires an `authorization-key` header for security.

## Customization Options

| Parameter | Description | Example Values |
|-----------|-------------|---------------|
| topic | Main subject of the video | "Sustainable Gardening" |
| goal | What the video aims to achieve | "Educate viewers about..." |
| email | Where to send the completed video | "user@example.com" |
| brand_name | For phonetic correction in captions | "GreenThumb" |
| voice_id | Text-to-speech voice to use | "alloy", "echo", "onyx" |
| caption_id | Caption style (0 = none) | "1", "2", "3" |
| background_music | Music track or category | "relaxed", "upbeat" |
| subtitle_position | Where captions appear | "bottom", "top" |
| text_effect | Caption animation style | "fadeIn", "typewriter" |
| add_brolls | Include B-roll footage | true, false |

## Architecture

The system consists of:
1. Task queue (Celery)
2. Content generation services
3. Media processing pipeline
4. Delivery mechanisms

## Troubleshooting

- Check logs with `docker-compose logs -f`
- Ensure all API keys are valid
- Verify S3 bucket permissions
- Make sure temp directory is writable

## License

[Aryan and Paresh]
