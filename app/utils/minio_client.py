from minio import Minio
from settings.config import settings
<<<<<<< HEAD
# Create a client with the MinIO server playground, its access key
   # and secret key.
# Initialize MinIO client
minio_client = Minio(
    settings.MINIO_ENDPOINT,
    access_key=settings.MINIO_ACCESS_KEY,
    secret_key=settings.MINIO_SECRET_KEY,
    secure=settings.MINIO_USE_SSL
)
 # Make 'demo' bucket if not exist.
found = minio_client.bucket_exists("demo")
if not found:
    minio_client.make_bucket("demo")
else:
    print("Bucket 'demo' already exists")


  # Upload the file

def upload_profile_picture(file_data, file_name):
    """
    Uploads a profile picture to MinIO.
    Args:
        file_data (bytes): File content to upload.
        file_name (str): Name of the file.
    Returns:
        str: URL to the uploaded file.
    Raises:
        ValueError: If the file type is unsupported.
    """
    # Validate file type
    allowed_extensions = {"jpg", "jpeg", "png", "gif"}
    file_extension = file_name.split(".")[-1].lower()
    if file_extension not in allowed_extensions:
        raise ValueError("Unsupported file type")

    minio_client.put_object(
        settings.MINIO_BUCKET_NAME,
        file_name,
        file_data,
        length=-1,
        part_size=10 * 1024 * 1024
    )
      #  file URL return 
    return f"{settings.MINIO_ENDPOINT}/{settings.MINIO_BUCKET_NAME}/{file_name}"
def get_profile_picture_url(file_name):
    """
    Generates a presigned URL for a profile picture.
    Args:
        file_name (str): Name of the file.
    Returns:
        str: Presigned URL for the file.
    """
    return minio_client.get_presigned_url('GET', settings.MINIO_BUCKET_NAME, file_name)
=======
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
>>>>>>> 0105224cc08bc3caf1fdf5a8be56e78a3b4f957f
