from minio import Minio
from settings.config import settings
from urllib.parse import urljoin

def _get_minio_client():
    # Create and return a MinIO client instance
    return Minio(
        endpoint=settings.MINIO_ENDPOINT,
        access_key=settings.MINIO_ACCESS_KEY,
        secret_key=settings.MINIO_SECRET_KEY,
        secure=settings.MINIO_USE_SSL,
    )

class ProfileImageService:
    """
    Handles storing profile images in a MinIO bucket and generating access URLs.
    """
    def __init__(self, client=None):
        self._endpoint = settings.MINIO_ENDPOINT
        self._bucket = settings.MINIO_BUCKET_NAME
        # Allow injection of a preconfigured client, else create one lazily
        self._client = client or _get_minio_client()

    def _ensure_bucket_exists(self):
        # Create bucket if it does not already exist
        if not self._client.bucket_exists(self._bucket):
            self._client.make_bucket(self._bucket)

    def store_image(self, content: bytes, filename: str) -> str:
        """
        Uploads an image file to the configured MinIO bucket.
        Raises ValueError for unsupported file extensions.
        Returns the publicly accessible URL of the stored image.
        """
        # Ensure bucket is ready
        self._ensure_bucket_exists()

        ext = filename.rsplit('.', 1)[-1].lower()
        if ext not in ('jpg', 'jpeg', 'png', 'gif'):
            raise ValueError(f"Invalid file extension: .{ext}")

        # Upload to MinIO with a 10 MB part size
        self._client.put_object(
            bucket_name=self._bucket,
            object_name=filename,
            data=content,
            length=-1,
            part_size=10 * 1024 * 1024,
        )

        # Construct and return the file URL
        return urljoin(f"{self._endpoint}/", f"{self._bucket}/{filename}")

    def generate_presigned_url(self, filename: str, expiry: int = 3600) -> str:
        """
        Creates a time-limited URL for accessing an image in the bucket.
        """
        return self._client.get_presigned_url(
            method='GET',
            bucket_name=self._bucket,
            object_name=filename,
            expires=expiry,
        )

# ——— Public API ———
# These functions defer to ProfileImageService but do not execute any network calls at import time.

def store_image(content: bytes, filename: str) -> str:
    """
    Store an image and return its URL.
    """
    service = ProfileImageService()
    return service.store_image(content, filename)


def generate_presigned_url(filename: str, expiry: int = 3600) -> str:
    """
    Generate a presigned URL for an image.
    """
    service = ProfileImageService()
    return service.generate_presigned_url(filename, expiry)
