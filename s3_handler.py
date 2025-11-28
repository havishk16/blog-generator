#!/usr/bin/env python3
"""
S3 Handler - Manages file uploads to AWS S3
"""

import os
import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from typing import Optional


class S3Handler:
    def __init__(self):
        """Initialize S3 client with credentials from environment variables"""
        self.bucket_name = os.getenv("AWS_S3_BUCKET_NAME")
        self.region = os.getenv("AWS_REGION", "us-east-1")
        
        # Check if S3 is configured
        aws_access_key = os.getenv("AWS_ACCESS_KEY_ID")
        aws_secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")
        
        self.enabled = all([self.bucket_name, aws_access_key, aws_secret_key])
        
        if not self.enabled:
            print("⚠️  AWS S3 credentials not found. S3 upload is disabled.")
            self.s3_client = None
            return
        
        try:
            # Initialize S3 client
            self.s3_client = boto3.client(
                's3',
                aws_access_key_id=aws_access_key,
                aws_secret_access_key=aws_secret_key,
                region_name=self.region
            )
            print(f"✓ S3 client initialized for bucket: {self.bucket_name}")
        except Exception as e:
            print(f"⚠️  Error initializing S3 client: {str(e)}")
            self.enabled = False
            self.s3_client = None
    
    def upload_file(self, file_path: str, s3_key: Optional[str] = None) -> Optional[str]:
        """
        Upload a file to S3 bucket
        
        Args:
            file_path: Local path to the file to upload
            s3_key: Optional S3 object key (path in bucket). If not provided, uses filename
            
        Returns:
            S3 URL of the uploaded file, or None if upload failed
        """
        if not self.enabled:
            print("S3 upload is disabled. Skipping upload.")
            return None
        
        if not os.path.exists(file_path):
            print(f"✗ File not found: {file_path}")
            return None
        
        # Use filename as S3 key if not provided
        if s3_key is None:
            s3_key = os.path.basename(file_path)
        
        try:
            # Upload file
            self.s3_client.upload_file(
                file_path,
                self.bucket_name,
                s3_key,
                ExtraArgs={'ContentType': 'application/pdf'}
            )
            
            # Generate S3 URL
            s3_url = f"https://{self.bucket_name}.s3.{self.region}.amazonaws.com/{s3_key}"
            print(f"✓ File uploaded to S3: {s3_url}")
            return s3_url
            
        except NoCredentialsError:
            print("✗ AWS credentials not available")
            return None
        except ClientError as e:
            print(f"✗ Error uploading to S3: {str(e)}")
            return None
        except Exception as e:
            print(f"✗ Unexpected error during S3 upload: {str(e)}")
            return None
    
    def generate_presigned_url(self, s3_key: str, expiration: int = 3600) -> Optional[str]:
        """
        Generate a presigned URL for temporary access to an S3 object
        
        Args:
            s3_key: S3 object key
            expiration: URL expiration time in seconds (default: 1 hour)
            
        Returns:
            Presigned URL, or None if generation failed
        """
        if not self.enabled:
            return None
        
        try:
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.bucket_name, 'Key': s3_key},
                ExpiresIn=expiration
            )
            return url
        except ClientError as e:
            print(f"✗ Error generating presigned URL: {str(e)}")
            return None
