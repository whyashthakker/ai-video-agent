import boto3
import logging
from dotenv import load_dotenv
import os
from datetime import datetime

# Load the environment variables
load_dotenv()

# Set the S3 credentials and config from environment variables
ACCESS_KEY = os.environ.get("AWS_ACCESS_KEY_ID")
SECRET_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY")
BUCKET_NAME = os.environ.get("AWS_BUCKET_NAME")
REGION_NAME = os.environ.get("AWS_REGION_NAME")
EXPIRATION = 86400

s3 = boto3.client(
    "s3",
    aws_access_key_id=ACCESS_KEY,
    aws_secret_access_key=SECRET_KEY,
    region_name=REGION_NAME,
)


def upload_zip_to_s3(zip_path, s3_path, userId, folder="shorts-data"):
    try:
        if not os.path.exists(zip_path):
            logging.error(f"Zipped file does not exist at {zip_path}")
            raise FileNotFoundError(f"Zipped file not found at {zip_path}")

        today = datetime.now().strftime("%Y-%m-%d")
        s3_path = f"{userId}/{today}/{folder}/{s3_path}"
        s3.upload_file(zip_path, BUCKET_NAME, s3_path)

    except Exception as e:
        logging.warning(f"Failed to upload zipped file to S3. Error: {str(e)}")
        raise


def upload_to_s3(local_path, s3_path, userId, folder="shorts"):
    try:
        # Check if file exists
        if not os.path.exists(local_path):
            logging.error(f"File does not exist at {local_path}")
            raise FileNotFoundError(f"File not found at {local_path}")

        # Generate today's date in YYYY-MM-DD format
        today = datetime.now().strftime("%Y-%m-%d")

        # Modify s3_path to include the userId, today's date, and the specified folder
        s3_path = f"{userId}/{today}/{folder}/{s3_path}"

        s3.upload_file(local_path, BUCKET_NAME, s3_path)

        # Generate a pre-signed URL for the uploaded file
        presigned_url = s3.generate_presigned_url(
            "get_object",
            Params={"Bucket": BUCKET_NAME, "Key": s3_path},
            ExpiresIn=EXPIRATION,
        )

        return presigned_url

    except Exception as e:
        logging.warning(f"Failed to upload to S3. Error: {str(e)}")
        raise
