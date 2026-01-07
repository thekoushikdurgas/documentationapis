"""Service layer for AWS S3 operations."""

from typing import Optional

import aioboto3
from botocore.exceptions import ClientError

from app.core.config import get_settings
from app.core.exceptions import S3Error
from app.utils.logger import get_logger

settings = get_settings()
logger = get_logger(__name__)


class S3Service:
    """Service for async S3 operations."""

    def __init__(self) -> None:
        """Initialize S3 service with settings."""
        self.bucket_name = settings.S3_BUCKET_NAME
        self.region = settings.AWS_REGION
        self.documentation_prefix = settings.S3_DOCUMENTATION_PREFIX
        self.presigned_expiration = settings.S3_PRESIGNED_URL_EXPIRATION

    def _get_session(self) -> aioboto3.Session:
        """Create and return an aioboto3 session."""
        return aioboto3.Session(
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=self.region,
        )

    async def upload_file(
        self,
        file_content: bytes,
        s3_key: str,
        content_type: Optional[str] = None,
    ) -> str:
        """
        Upload a file to S3.

        Args:
            file_content: The file content as bytes
            s3_key: The S3 key (path) where the file should be stored
            content_type: Optional content type (MIME type) for the file

        Returns:
            The S3 key where the file was uploaded

        Raises:
            S3Error: If upload fails
        """
        if not self.bucket_name:
            raise S3Error("S3_BUCKET_NAME is not configured")

        session = self._get_session()
        try:
            async with session.client("s3") as s3_client:
                upload_kwargs = {
                    "Bucket": self.bucket_name,
                    "Key": s3_key,
                    "Body": file_content,
                }
                if content_type:
                    upload_kwargs["ContentType"] = content_type

                await s3_client.put_object(**upload_kwargs)
                logger.info(f"Uploaded file to S3: {s3_key}")
                return s3_key
        except ClientError as exc:
            error_msg = f"Failed to upload file to S3: {str(exc)}"
            logger.error(error_msg, exc_info=True)
            raise S3Error(error_msg) from exc
        except Exception as exc:
            error_msg = f"Unexpected error uploading file to S3: {str(exc)}"
            logger.error(error_msg, exc_info=True)
            raise S3Error(error_msg) from exc

    async def download_file(self, s3_key: str) -> bytes:
        """
        Download a file from S3.

        Args:
            s3_key: The S3 key (path) of the file to download

        Returns:
            The file content as bytes

        Raises:
            S3Error: If download fails
            FileNotFoundError: If file doesn't exist
        """
        if not self.bucket_name:
            raise S3Error("S3_BUCKET_NAME is not configured")

        session = self._get_session()
        try:
            async with session.client("s3") as s3_client:
                response = await s3_client.get_object(Bucket=self.bucket_name, Key=s3_key)
                file_content = await response["Body"].read()
                logger.info(f"Downloaded file from S3: {s3_key}")
                return file_content
        except ClientError as exc:
            error_code = exc.response.get("Error", {}).get("Code", "")
            if error_code == "NoSuchKey":
                raise FileNotFoundError(f"File not found in S3: {s3_key}") from exc
            error_msg = f"Failed to download file from S3: {str(exc)}"
            logger.error(error_msg, exc_info=True)
            raise S3Error(error_msg) from exc
        except Exception as exc:
            error_msg = f"Unexpected error downloading file from S3: {str(exc)}"
            logger.error(error_msg, exc_info=True)
            raise S3Error(error_msg) from exc

    async def delete_file(self, s3_key: str) -> bool:
        """
        Delete a file from S3.

        Args:
            s3_key: The S3 key (path) of the file to delete

        Returns:
            True if deleted successfully, False if file doesn't exist

        Raises:
            S3Error: If deletion fails
        """
        if not self.bucket_name:
            raise S3Error("S3_BUCKET_NAME is not configured")

        session = self._get_session()
        try:
            async with session.client("s3") as s3_client:
                await s3_client.delete_object(Bucket=self.bucket_name, Key=s3_key)
                logger.info(f"Deleted file from S3: {s3_key}")
                return True
        except ClientError as exc:
            error_code = exc.response.get("Error", {}).get("Code", "")
            if error_code == "NoSuchKey":
                # File doesn't exist, return False
                logger.warning(f"File not found in S3 for deletion: {s3_key}")
                return False
            error_msg = f"Failed to delete file from S3: {str(exc)}"
            logger.error(error_msg, exc_info=True)
            raise S3Error(error_msg) from exc
        except Exception as exc:
            error_msg = f"Unexpected error deleting file from S3: {str(exc)}"
            logger.error(error_msg, exc_info=True)
            raise S3Error(error_msg) from exc

    async def bucket_exists(self) -> bool:
        """
        Check if the configured S3 bucket exists and is accessible.

        Returns:
            True if bucket exists and is accessible, False otherwise

        Raises:
            S3Error: If there's an error checking the bucket (other than not existing)
        """
        if not self.bucket_name:
            raise S3Error("S3_BUCKET_NAME is not configured")

        session = self._get_session()
        try:
            async with session.client("s3") as s3_client:
                await s3_client.head_bucket(Bucket=self.bucket_name)
                logger.info(f"Bucket '{self.bucket_name}' exists and is accessible")
                return True
        except ClientError as exc:
            error_code = exc.response.get("Error", {}).get("Code", "")
            if error_code == "404":
                # Bucket doesn't exist
                logger.info(f"Bucket '{self.bucket_name}' does not exist")
                return False
            elif error_code == "403":
                # Access denied - bucket might exist but no permission
                error_msg = f"Access denied to bucket '{self.bucket_name}' - check IAM permissions"
                logger.error(error_msg)
                raise S3Error(error_msg) from exc
            else:
                error_msg = f"Error checking bucket existence: {str(exc)}"
                logger.error(error_msg, exc_info=True)
                raise S3Error(error_msg) from exc
        except Exception as exc:
            error_msg = f"Unexpected error checking bucket existence: {str(exc)}"
            logger.error(error_msg, exc_info=True)
            raise S3Error(error_msg) from exc

    async def create_bucket(self) -> bool:
        """
        Create the configured S3 bucket if it doesn't exist.

        Returns:
            True if bucket was created or already exists, False otherwise

        Raises:
            S3Error: If bucket creation fails
        """
        if not self.bucket_name:
            raise S3Error("S3_BUCKET_NAME is not configured")

        # Check if bucket already exists
        try:
            if await self.bucket_exists():
                logger.info(f"Bucket '{self.bucket_name}' already exists")
                return True
        except S3Error as exc:
            # If bucket_exists raised an error (not just doesn't exist), re-raise it
            if "Access denied" in str(exc) or "Error checking" in str(exc):
                raise

        session = self._get_session()
        try:
            async with session.client("s3") as s3_client:
                # For regions other than us-east-1, we need to specify location constraint
                create_kwargs = {"Bucket": self.bucket_name}
                
                if self.region and self.region != "us-east-1":
                    create_kwargs["CreateBucketConfiguration"] = {
                        "LocationConstraint": self.region
                    }

                await s3_client.create_bucket(**create_kwargs)
                logger.info(f"Created bucket '{self.bucket_name}' in region '{self.region}'")
                return True
        except ClientError as exc:
            error_code = exc.response.get("Error", {}).get("Code", "")
            if error_code == "BucketAlreadyExists":
                # Bucket was created between check and creation
                logger.info(f"Bucket '{self.bucket_name}' already exists (created concurrently)")
                return True
            elif error_code == "BucketAlreadyOwnedByYou":
                # Bucket already owned by this account
                logger.info(f"Bucket '{self.bucket_name}' is already owned by you")
                return True
            else:
                error_msg = f"Failed to create bucket '{self.bucket_name}': {str(exc)}"
                logger.error(error_msg, exc_info=True)
                raise S3Error(error_msg) from exc
        except Exception as exc:
            error_msg = f"Unexpected error creating bucket: {str(exc)}"
            logger.error(error_msg, exc_info=True)
            raise S3Error(error_msg) from exc

    async def generate_presigned_url(
        self,
        s3_key: str,
        expiration: Optional[int] = None,
    ) -> str:
        """
        Generate a presigned URL for S3 object access.

        Args:
            s3_key: The S3 key (path) of the file
            expiration: URL expiration time in seconds (defaults to configured value)

        Returns:
            Presigned URL string

        Raises:
            S3Error: If URL generation fails
        """
        if not self.bucket_name:
            raise S3Error("S3_BUCKET_NAME is not configured")

        expiration = expiration or self.presigned_expiration

        session = self._get_session()
        try:
            async with session.client("s3") as s3_client:
                url = await s3_client.generate_presigned_url(
                    "get_object",
                    Params={"Bucket": self.bucket_name, "Key": s3_key},
                    ExpiresIn=expiration,
                )
                logger.info(f"Generated presigned URL for S3 key: {s3_key}")
                return url
        except ClientError as exc:
            error_msg = f"Failed to generate presigned URL: {str(exc)}"
            logger.error(error_msg, exc_info=True)
            raise S3Error(error_msg) from exc
        except Exception as exc:
            error_msg = f"Unexpected error generating presigned URL: {str(exc)}"
            logger.error(error_msg, exc_info=True)
            raise S3Error(error_msg) from exc

