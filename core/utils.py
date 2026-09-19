import io
import os
from PIL import Image
from django.core.files.base import ContentFile
from django.conf import settings


ALLOWED_MIME_TYPES = {
    'image/jpeg': '.jpg',
    'image/jpg': '.jpg',
    'image/png': '.png',
    'image/webp': '.webp',
}

MAX_FILE_SIZE = 25 * 1024 * 1024  # 25 MB max file size limit


def process_and_validate_image(uploaded_file):
    """
    Validates uploaded image binary using Pillow, extracts resolution and metadata,
    and returns (validated_image_file, width, height, file_size, mime_type, thumbnail_file).
    """
    # 1. Check file size
    file_size = uploaded_file.size
    if file_size > MAX_FILE_SIZE:
        raise ValueError(f"File size exceeds maximum limit of 25MB ({file_size} bytes uploaded).")

    # 2. Verify image using Pillow
    try:
        image = Image.open(uploaded_file)
        image.verify()
        # Re-open after verify() as verify() corrupts the Pillow instance
        uploaded_file.seek(0)
        image = Image.open(uploaded_file)
    except Exception as e:
        raise ValueError("Invalid image file or corrupted binary data.") from e

    width, height = image.size
    fmt = (image.format or 'JPEG').upper()
    mime_type = f"image/{fmt.lower()}"
    if mime_type not in ALLOWED_MIME_TYPES:
        mime_type = 'image/jpeg'

    # 3. Generate thumbnail (WebP format, 300x300 max bounding box)
    uploaded_file.seek(0)
    thumb_img = Image.open(uploaded_file)
    if thumb_img.mode in ('RGBA', 'LA', 'P'):
        thumb_img = thumb_img.convert('RGB')
    
    thumb_img.thumbnail((300, 300), Image.Resampling.LANCZOS)
    thumb_io = io.BytesIO()
    thumb_img.save(thumb_io, format='WEBP', quality=85)
    thumb_filename = f"thumb_{os.path.splitext(uploaded_file.name)[0]}.webp"
    thumbnail_file = ContentFile(thumb_io.getvalue(), name=thumb_filename)

    uploaded_file.seek(0)
    return uploaded_file, width, height, file_size, mime_type, thumbnail_file


def get_signed_media_url(photo, is_thumbnail=False, request=None):
    """
    Generates a secure temporary URL for an image.
    In R2 production, uses presigned URL.
    In local dev, uses Django's authorized private media serving view.
    """
    if getattr(settings, 'USE_R2_STORAGE', False):
        target_file = photo.thumbnail if (is_thumbnail and photo.thumbnail) else photo.image
        try:
            return target_file.url
        except Exception:
            pass

    # Local development private serving endpoint
    photo_type = 'thumb' if is_thumbnail else 'original'
    return f"/media/private/{photo.id}/{photo_type}/"
