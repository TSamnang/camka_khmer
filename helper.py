import os
import shutil
import uuid
from PIL import Image, ImageOps
from werkzeug.utils import secure_filename

# Base directory for uploads
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "public", "static") if os.path.exists(os.path.join(BASE_DIR, "public", "static")) else os.path.join(BASE_DIR, "static")
UPLOAD_ORG_DIR = os.path.join(STATIC_DIR, "uploads", "org")
UPLOAD_THUMB_DIR = os.path.join(STATIC_DIR, "uploads", "thumb")

# Ensure upload directories exist
os.makedirs(UPLOAD_ORG_DIR, exist_ok=True)
os.makedirs(UPLOAD_THUMB_DIR, exist_ok=True)

ALLOWED_EXT = {"png", "jpg", "jpeg", "gif", "webp"}


def allowed(name):
    return "." in name and name.rsplit(".", 1)[-1].lower() in ALLOWED_EXT


allowed_file = allowed


def create_thumb_50(org_path, thumb_path, ext=None):
    """
    Creates a 50% quality thumbnail:
    - Resized to 50% of the original dimensions using high quality Lanczos filtering.
    - Compressed at 50% quality for optimal web performance without visual blur.
    """
    if not ext:
        ext = org_path.rsplit(".", 1)[-1].lower()

    try:
        with Image.open(org_path) as image:
            # Handle orientation from EXIF metadata
            image = ImageOps.exif_transpose(image)

            width, height = image.size
            new_width = max(1, int(width * 0.5))
            new_height = max(1, int(height * 0.5))

            thumb_image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)

            # Convert non-RGB mode (RGBA, LA, P, etc.) to RGB for JPEG format
            if ext in ("jpg", "jpeg") and thumb_image.mode != "RGB":
                thumb_image = thumb_image.convert("RGB")

            if ext in ("jpg", "jpeg"):
                thumb_image.save(thumb_path, quality=50, optimize=True)
            elif ext == "webp":
                thumb_image.save(thumb_path, quality=50, method=4)
            else:
                thumb_image.save(thumb_path, optimize=True)
    except Exception as e:
        print(f"Error creating 50% thumbnail: {e}")
        if not os.path.exists(thumb_path):
            shutil.copyfile(org_path, thumb_path)


def save_profile_image(file):
    """
    Saves an uploaded image:
    1. Full 100% original quality saved into static/uploads/org/
    2. 50% quality image saved into static/uploads/thumb/
    Returns the unique filename.
    """
    if not file or not file.filename or not allowed(file.filename):
        return None

    os.makedirs(UPLOAD_ORG_DIR, exist_ok=True)
    os.makedirs(UPLOAD_THUMB_DIR, exist_ok=True)

    ext = file.filename.rsplit(".", 1)[-1].lower()
    raw_name = secure_filename(file.filename)
    unique_prefix = uuid.uuid4().hex[:12]

    if raw_name:
        filename = f"{unique_prefix}_{raw_name}"
    else:
        filename = f"{unique_prefix}.{ext}"

    org_path = os.path.join(UPLOAD_ORG_DIR, filename)
    thumb_path = os.path.join(UPLOAD_THUMB_DIR, filename)

    # 1. Save original image (100% full quality)
    file.save(org_path)

    # 2. Create 50% quality image in thumb/
    create_thumb_50(org_path, thumb_path, ext)

    return filename


save_image = save_profile_image


def sync_all_uploads():
    """
    Ensures all images in static/uploads/org have their corresponding
    50% quality version in static/uploads/thumb.
    """
    if not os.path.exists(UPLOAD_ORG_DIR):
        return
    for fname in os.listdir(UPLOAD_ORG_DIR):
        org_file = os.path.join(UPLOAD_ORG_DIR, fname)
        thumb_file = os.path.join(UPLOAD_THUMB_DIR, fname)
        if os.path.isfile(org_file):
            create_thumb_50(org_file, thumb_file)
