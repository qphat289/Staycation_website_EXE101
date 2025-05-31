import boto3
import os
from botocore.exceptions import ClientError
from werkzeug.utils import secure_filename
from datetime import datetime

class S3Handler:
    def __init__(self, aws_access_key_id, aws_secret_access_key, region_name, bucket_name):
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            region_name=region_name
        )
        self.bucket_name = bucket_name

    def upload_file(self, file, folder=""):
        """
        Upload a file to S3 bucket
        Returns: URL of the uploaded file if successful, None otherwise
        """
        try:
            # Generate secure filename with timestamp
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            filename = secure_filename(file.filename)
            s3_filename = f"{folder}/{timestamp}_{filename}" if folder else f"{timestamp}_{filename}"

            # Upload file
            self.s3_client.upload_fileobj(file, self.bucket_name, s3_filename)

            # Generate URL
            url = f"https://{self.bucket_name}.s3.amazonaws.com/{s3_filename}"
            return url

        except ClientError as e:
            print(f"Error uploading file to S3: {str(e)}")
            return None

    def delete_file(self, file_url):
        """
        Delete a file from S3 bucket using its URL
        """
        try:
            # Extract key from URL
            s3_key = file_url.split(f"{self.bucket_name}.s3.amazonaws.com/")[1]
            
            # Delete file
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=s3_key
            )
            return True
        except Exception as e:
            print(f"Error deleting file from S3: {str(e)}")
            return False 