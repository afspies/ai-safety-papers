"""Cloudflare R2 client for storing and retrieving files."""
import boto3
import logging
import os
from typing import Optional, Dict, Any
from pathlib import Path
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)

class CloudflareR2Client:
    """Client for Cloudflare R2 storage operations."""
    
    def __init__(self, account_id: str = None, access_key_id: str = None, 
                 access_key_secret: str = None, bucket_name: str = None):
        """
        Initialize the Cloudflare R2 client.
        
        Args:
            account_id: Cloudflare account ID
            access_key_id: R2 access key ID
            access_key_secret: R2 access key secret
            bucket_name: R2 bucket name
        """
        # If params not provided, try to load from config/env
        if not all([account_id, access_key_id, access_key_secret, bucket_name]):
            # Try to import from different possible module paths
            try:
                from utils.config_loader import load_config
            except ImportError:
                try:
                    from src.utils.config_loader import load_config
                except ImportError:
                    from backend.src.utils.config_loader import load_config
                    
            config = load_config()
            r2_config = config.get('cloudflare_r2', {})
            
            account_id = os.environ.get("R2_ACCOUNT_ID") or r2_config.get('account_id')
            access_key_id = os.environ.get("R2_ACCESS_KEY_ID") or r2_config.get('access_key_id')
            access_key_secret = os.environ.get("R2_ACCESS_KEY_SECRET") or r2_config.get('access_key_secret')
            bucket_name = os.environ.get("R2_BUCKET") or r2_config.get('bucket_name')
            self.public_url_prefix = os.environ.get("R2_PUBLIC_URL_PREFIX") or r2_config.get('public_url_prefix')
            
        if not all([account_id, access_key_id, access_key_secret, bucket_name]):
            raise ValueError("Cloudflare R2 credentials are required")
            
        self.account_id = account_id
        self.bucket_name = bucket_name
        
        # Initialize S3 client (R2 uses S3-compatible API)
        endpoint_url = f"https://{account_id}.r2.cloudflarestorage.com"
        self.client = boto3.client(
            's3',
            endpoint_url=endpoint_url,
            aws_access_key_id=access_key_id,
            aws_secret_access_key=access_key_secret,
            region_name='auto'  # R2 ignores this but it's required by boto3
        )
        logger.info(f"Initialized Cloudflare R2 client for bucket: {bucket_name}")
        
    def upload_file(self, file_data: bytes, key: str, content_type: str = None) -> Optional[str]:
        """
        Upload a file to R2 storage.
        
        Args:
            file_data: File data as bytes
            key: The object key (path in bucket)
            content_type: MIME type of the file
            
        Returns:
            Public URL of the uploaded file if successful, None otherwise
        """
        try:
            extra_args = {
                # Cache for 1 year (immutable content)
                'CacheControl': 'public, max-age=31536000, immutable',
            }
            
            if content_type:
                extra_args['ContentType'] = content_type
                
            self.client.put_object(
                Bucket=self.bucket_name,
                Key=key,
                Body=file_data,
                **extra_args
            )
            
            # Generate the public URL
            if self.public_url_prefix:
                # Use the configured public URL (e.g., assets.afspies.com/figures/paper_id/fig1.png)
                public_url = f"{self.public_url_prefix}/{key.replace('figures/', '')}"
            else:
                # Fall back to direct R2 URL if no public URL prefix is configured
                public_url = f"https://{self.bucket_name}.{self.account_id}.r2.cloudflarestorage.com/{key}"
            logger.debug(f"Uploaded file to R2: {key}, public URL: {public_url}")
            return public_url
        except Exception as e:
            logger.error(f"Error uploading file to R2: {e}")
            return None
            
    def download_file(self, key: str) -> Optional[bytes]:
        """
        Download a file from R2 storage.
        
        Args:
            key: The object key (path in bucket)
            
        Returns:
            File data as bytes if successful, None otherwise
        """
        try:
            response = self.client.get_object(
                Bucket=self.bucket_name,
                Key=key
            )
            
            # Read the file data
            file_data = response['Body'].read()
            logger.debug(f"Downloaded file from R2: {key}")
            return file_data
        except ClientError as e:
            logger.error(f"Error downloading file from R2: {e}")
            return None
            
    def delete_file(self, key: str) -> bool:
        """
        Delete a file from R2 storage.
        
        Args:
            key: The object key (path in bucket)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.client.delete_object(
                Bucket=self.bucket_name,
                Key=key
            )
            logger.debug(f"Deleted file from R2: {key}")
            return True
        except Exception as e:
            logger.error(f"Error deleting file from R2: {e}")
            return False
            
    def generate_presigned_url(self, key: str, expiration: int = 3600) -> Optional[str]:
        """
        Generate a presigned URL for direct access to a file.
        
        Args:
            key: The object key (path in bucket)
            expiration: URL expiration time in seconds (default: 1 hour)
            
        Returns:
            Presigned URL if successful, None otherwise
        """
        try:
            url = self.client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': self.bucket_name,
                    'Key': key
                },
                ExpiresIn=expiration
            )
            logger.debug(f"Generated presigned URL for R2 object: {key}")
            return url
        except Exception as e:
            logger.error(f"Error generating presigned URL: {e}")
            return None