# cleaner/metadata_analyzer.py
import exifread
from pypdf import PdfReader
from docx import Document
import math

def _dms_to_decimal(dms, ref):
    """
    Convert exifread DMS tuple to decimal degrees.
    dms is something like [(deg_num, deg_den), (min_num,min_den), (sec_num,sec_den)]
    ref is 'N','S','E','W'
    """
    try:
        degrees = dms[0].num / dms[0].den
        minutes = dms[1].num / dms[1].den
        seconds = dms[2].num / dms[2].den
        dec = degrees + minutes / 60.0 + seconds / 3600.0
        if ref in ['S', 'W', 's', 'w']:
            dec = -dec
        return round(dec, 6)
    except Exception:
        return None

def _friendly_label(tag_name):
    """Simple mapping of common EXIF/PDF/DOCX keys to friendlier labels."""
    mapping = {
        "Image Make": "Camera Make",
        "Image Model": "Camera Model",
        "EXIF DateTimeOriginal": "Original Date/Time",
        "EXIF DateTimeDigitized": "Digital Date/Time",
        "EXIF ExifImageWidth": "Image Width",
        "EXIF ExifImageLength": "Image Height",
        "EXIF FNumber": "Aperture (FNumber)",
        "EXIF ExposureTime": "Exposure Time",
        "EXIF ISOSpeedRatings": "ISO",
        "EXIF FocalLength": "Focal Length",
        "Image Software": "Software",
        "GPS GPSLatitude": "GPS Latitude (DMS)",
        "GPS GPSLongitude": "GPS Longitude (DMS)",
        "GPS GPSLatitudeRef": "GPS Latitude Ref",
        "GPS GPSLongitudeRef": "GPS Longitude Ref",
        "GPS GPSAltitude": "GPS Altitude",
        # PDF/Docx friendly names
        "Author": "Author",
        "Title": "Title",
        "Subject": "Subject",
        "Keywords": "Keywords",
        "LastModifiedBy": "Last Modified By",
        "creator": "Creator",
    }
    return mapping.get(tag_name, tag_name)

def extract_metadata(filepath, ext):
    """
    Returns:
        {
            "raw": { ... },                # original metadata (string values)
            "pretty": { "label": "value", ... }  # friendly, concise metadata for display
        }
    """
    raw = {}
    pretty = {}

    try:
        if ext in ["jpg", "jpeg", "png"]:
            with open(filepath, "rb") as f:
                tags = exifread.process_file(f, details=False)

                # convert tags to strings but skip thumbnail and huge maker notes
                for tag, val in tags.items():
                    t_low = tag.lower()
                    if "thumbnail" in t_low:
                        continue
                    if tag.lower().startswith("maker") and len(str(val)) > 500:
                        continue
                    raw[tag] = str(val)

                # friendly fields
                # camera make/model
                for key in ("Image Make", "Image Model"):
                    if key in tags:
                        pretty[_friendly_label(key)] = str(tags.get(key))

                # date/time
                for key in ("EXIF DateTimeOriginal", "EXIF DateTimeDigitized"):
                    if key in tags:
                        pretty[_friendly_label(key)] = str(tags.get(key))

                # exposure / fnumber / iso
                if "EXIF FNumber" in tags:
                    pretty["Aperture"] = str(tags.get("EXIF FNumber"))
                if "EXIF ExposureTime" in tags:
                    pretty["Exposure Time"] = str(tags.get("EXIF ExposureTime"))
                if "EXIF ISOSpeedRatings" in tags:
                    pretty["ISO"] = str(tags.get("EXIF ISOSpeedRatings"))
                if "EXIF FocalLength" in tags:
                    pretty["Focal Length"] = str(tags.get("EXIF FocalLength"))

                # image dimensions
                if "EXIF ExifImageWidth" in tags:
                    pretty["Image Width"] = str(tags.get("EXIF ExifImageWidth"))
                if "EXIF ExifImageLength" in tags:
                    pretty["Image Height"] = str(tags.get("EXIF ExifImageLength"))

                # GPS parsing — if present, produce decimal lat/lon
                gps_lat = tags.get("GPS GPSLatitude")
                gps_lat_ref = tags.get("GPS GPSLatitudeRef")
                gps_lon = tags.get("GPS GPSLongitude")
                gps_lon_ref = tags.get("GPS GPSLongitudeRef")
                gps_alt = tags.get("GPS GPSAltitude")

                if gps_lat and gps_lat_ref and gps_lon and gps_lon_ref:
                    # exifread returns values as Ratio objects in a list-like container
                    lat_dec = _dms_to_decimal(gps_lat.values, str(gps_lat_ref))
                    lon_dec = _dms_to_decimal(gps_lon.values, str(gps_lon_ref))
                    if lat_dec is not None and lon_dec is not None:
                        pretty["GPS Latitude (decimal)"] = lat_dec
                        pretty["GPS Longitude (decimal)"] = lon_dec
                        # keep original DMS as well
                        pretty["GPS (DMS)"] = f"{str(gps_lat)} , {str(gps_lon)}"
                elif gps_alt:
                    pretty["GPS Altitude"] = str(gps_alt)

                # If pretty still empty, fill with a few common raw fields for user friendliness
                # Map some raw tags
                common_keys = ["Image Make", "Image Model", "EXIF DateTimeOriginal", "EXIF ISOSpeedRatings"]
                for k in common_keys:
                    if k in raw and _friendly_label(k) not in pretty:
                        pretty[_friendly_label(k)] = raw[k]

        elif ext == "pdf":
            reader = PdfReader(filepath)
            if reader.metadata:
                # keys start with /Title etc.
                for k, v in reader.metadata.items():
                    kname = k[1:] if k.startswith("/") else k
                    raw[kname] = str(v)
                    # map to pretty if useful
                    if kname in ("Title", "Author", "Subject", "Creator", "Producer"):
                        pretty[kname] = str(v)

        elif ext == "docx":
            doc = Document(filepath)
            p = doc.core_properties
            # raw
            core = {
                "author": p.author,
                "title": p.title,
                "subject": p.subject,
                "keywords": p.keywords,
                "last_modified_by": p.last_modified_by,
                "created": str(p.created) if p.created else None,
                "modified": str(p.modified) if p.modified else None,
                "category": p.category,
                "comments": p.comments,
                "revision": p.revision,
            }
            for k, v in core.items():
                if v and v != "None":
                    raw[k] = str(v)
                    # make pretty labels
                    pretty_label = k.replace("_", " ").title()
                    pretty[pretty_label] = str(v)

    except Exception as e:
        raw["__error__"] = f"Extraction failed: {str(e)}"

    # remove empty values
    raw = {k: v for k, v in raw.items() if v and v != "None"}
    pretty = {k: v for k, v in pretty.items() if v and v != "None"}

    return {"raw": raw, "pretty": pretty}
    

def infer_privacy_risks(metadata_dict):
    """
    metadata_dict is the 'raw' metadata dict or combined string.
    Returns: {"inferences": [...], "score": int}
    """
    # Accept either raw dict or the structure returned above
    raw = metadata_dict if isinstance(metadata_dict, dict) else {}
    # if user passed the wrapper with 'raw' key:
    if "raw" in raw and isinstance(raw["raw"], dict):
        raw = raw["raw"]

    meta_keys = " ".join(raw.keys()).lower()
    meta_vals = " ".join(str(v).lower() for v in raw.values())
    meta_text = meta_keys + " " + meta_vals

    inferences = []
    score = 0

    if "gps" in meta_text or "gpslatitude" in meta_text or "gpslongitude" in meta_text:
        inferences.append("📍 GPS data detected — location may be exposed.")
        score += 5

    if "author" in meta_text or "creator" in meta_text or "lastmodifiedby" in meta_text:
        inferences.append("👤 Author / creator info found — identity could be revealed.")
        score += 2

    if "make" in meta_text or "model" in meta_text or "camera" in meta_text:
        inferences.append("📸 Device or camera details present — device fingerprinting possible.")
        score += 1

    if "date" in meta_text or "created" in meta_text or "modified" in meta_text:
        inferences.append("🕒 Timestamps found — creation/edit time exposed.")
        score += 1

    if "@" in meta_vals or "email" in meta_text:
        inferences.append("✉️ Email address or username found — PII risk.")
        score += 2

    if score == 0:
        inferences.append("✅ No obvious sensitive metadata detected. Low risk.")

    if score > 10:
        score = 10

    return {"inferences": inferences, "score": int(score)}
