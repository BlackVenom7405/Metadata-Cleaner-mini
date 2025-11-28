from PIL import Image
import piexif
import io

def clean_image(input_path, output_path):
    """
    Remove EXIF metadata from an image by rewriting pixel data.
    Also explicitly remove EXIF using piexif where available.
    """
    with Image.open(input_path) as img:
        # Create a new image with same mode & size, put pixel data (strips EXIF)
        data = list(img.getdata())
        clean_img = Image.new(img.mode, img.size)
        clean_img.putdata(data)

        # Save without exif first
        clean_img.save(output_path)

    # Also try to remove any remaining EXIF with piexif (safe if no exif)
    try:
        piexif.remove(output_path)
    except Exception:
        # If piexif fails, ignore (image already re-saved without EXIF)
        pass

    return output_path
