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


```mermaid
flowchart TD
    %% Main flow
    Start([Start]) --> InputProcessing["Process Task Information\n(topic, goal, user preferences)"]
    InputProcessing --> UserMedia{"User Media\nProvided?"}
    
    %% User media handling
    UserMedia -->|"Yes"| DownloadUserMedia["Download User Media\n(images, audio)"]
    UserMedia -->|"No"| ScriptCheck
    DownloadUserMedia --> ScriptCheck
    
    %% Script processing
    ScriptCheck{"User Script\nProvided?"}
    ScriptCheck -->|"Yes"| CleanScript["Clean User Script"]
    ScriptCheck -->|"No"| GeneratePrompt["Generate Prompt\nfrom Topic & Goal"]
    
    CleanScript --> FetchContent
    GeneratePrompt --> FetchContent
    
    %% Content generation
    FetchContent["Fetch Image Descriptions & Script\nvia ChatGPT API"]
    FetchContent --> ValidateSegments{"More than\n12 segments?"}
    ValidateSegments -->|"Yes"| RetryFetch["Retry Fetch\n(limited to 2 attempts)"]
    RetryFetch --> FetchContent
    
    ValidateSegments -->|"No"| GenerateAudio["Generate Audio Files\nfor Each Text Segment"]
    GenerateAudio --> GenerateImages["Generate Images\n(skip for user-provided ones)"]
    GenerateImages --> CombineMedia["Combine Images & Audio\ninto Base Video"]
    
    %% Caption processing
    CombineMedia --> CaptionCheck{"Captions\nEnabled?"}
    
    CaptionCheck -->|"Yes"| ExtractAudio["Extract Audio\nfrom Video"]
    ExtractAudio --> TranscribeAudio["Transcribe Audio\nwith OpenAI"]
    
    TranscribeAudio --> BrandCheck{"Brand Name\nProvided?"}
    BrandCheck -->|"Yes"| PhoneticCorrection["Apply Phonetic\nCorrections"]
    BrandCheck -->|"No"| GenerateCaptionedVideo
    PhoneticCorrection --> GenerateCaptionedVideo
    
    GenerateCaptionedVideo["Generate Video with\nCaptions & Watermark"]
    GenerateCaptionedVideo --> MusicCheck
    
    CaptionCheck -->|"No"| MusicCheck
    
    %% Final enhancements
    MusicCheck{"Background\nMusic?"}
    MusicCheck -->|"Yes"| AddMusic["Add Background Music"]
    MusicCheck -->|"No"| UploadToS3
    AddMusic --> UploadToS3
    
    %% Delivery
    UploadToS3["Upload Final Video\nto S3 Storage"]
    UploadToS3 --> S3Error{"Upload\nSuccessful?"}
    S3Error -->|"No"| LogS3Error["Log S3 Error\n& Re-throw Exception"]
    S3Error -->|"Yes"| NotifyUser
    
    NotifyUser["Send Email Notification\nto User"]
    NotifyUser --> EmailError{"Email\nSent?"}
    EmailError -->|"No"| LogEmailError["Log Email Error\n& Continue"]
    EmailError -->|"Yes"| TriggerWebhook
    LogEmailError --> TriggerWebhook
    
    TriggerWebhook["Trigger Webhook\nfor System Integration"]
    TriggerWebhook --> WebhookError{"Webhook\nTriggered?"}
    WebhookError -->|"No"| LogWebhookError["Log Webhook Error\n& Continue"]
    WebhookError -->|"Yes"| CleanupFiles
    LogWebhookError --> CleanupFiles
    
    %% Cleanup
    CleanupFiles["Zip Temporary Files"]
    CleanupFiles --> UploadZip["Upload Zip to S3\n(commented out in code)"]
    UploadZip --> DeleteTempFiles["Delete Temporary Files\n(commented out in code)"]
    DeleteTempFiles --> End([End])
    
    %% Error handling
    LogS3Error --> End
    
    %% Global error handling
    ProcessingError["Process Error:\n1. Log Error Message\n2. Trigger Failure Webhook"]
    
    InputProcessing -->|"Error"| ProcessingError
    DownloadUserMedia -->|"Error"| ProcessingError
    CleanScript -->|"Error"| ProcessingError
    GeneratePrompt -->|"Error"| ProcessingError
    FetchContent -->|"Error"| ProcessingError
    GenerateAudio -->|"Error"| ProcessingError
    GenerateImages -->|"Error"| ProcessingError
    CombineMedia -->|"Error"| ProcessingError
    ExtractAudio -->|"Error"| ProcessingError
    TranscribeAudio -->|"Error"| ProcessingError
    PhoneticCorrection -->|"Error"| ProcessingError
    GenerateCaptionedVideo -->|"Error"| ProcessingError
    AddMusic -->|"Error"| ProcessingError
    
    ProcessingError --> CleanupFiles
    
    %% Style definitions
    classDef start fill:#4CAF50,stroke:#388E3C,color:white;
    classDef end fill:#F44336,stroke:#D32F2F,color:white;
    classDef process fill:#E3F2FD,stroke:#1976D2,color:#0D47A1;
    classDef decision fill:#FFF9C4,stroke:#FBC02D,color:#5D4037;
    classDef error fill:#FFEBEE,stroke:#C62828,color:#B71C1C;
    classDef success fill:#E8F5E9,stroke:#388E3C,color:#1B5E20;
    
    class Start,End start;
    class End end;
    class InputProcessing,DownloadUserMedia,CleanScript,GeneratePrompt,FetchContent,GenerateAudio,GenerateImages,CombineMedia,ExtractAudio,TranscribeAudio,PhoneticCorrection,GenerateCaptionedVideo,AddMusic,UploadToS3,NotifyUser,TriggerWebhook,CleanupFiles,UploadZip,DeleteTempFiles process;
    class UserMedia,ScriptCheck,ValidateSegments,CaptionCheck,BrandCheck,MusicCheck,S3Error,EmailError,WebhookError decision;
    class ProcessingError,LogS3Error,LogEmailError,LogWebhookError error;
    class RetryFetch success;
```

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
