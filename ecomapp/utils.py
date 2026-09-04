import os


def get_media_duration(file_path, media_type):
    """Return audio/video duration without bundling MoviePy/FFmpeg/NumPy.

    Mutagen can read duration metadata for the audio formats used by this project
    and for common MP4/M4A containers. If a format is unsupported, the UI falls
    back to 0:00 instead of making the deployment depend on a ~100 MB FFmpeg stack.
    """
    try:
        if media_type in {"audio", "video"}:
            from mutagen import File as MutagenFile

            media = MutagenFile(file_path)
            length = getattr(getattr(media, "info", None), "length", None)
            if length:
                return format_duration(length)
    except Exception:
        pass
    return "0:00"


def format_duration(seconds):
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{minutes}:{secs:02d}"


def extract_text_from_file(file_path):
    ext = os.path.splitext(file_path)[1].lower()

    try:
        if ext == ".docx":
            return extract_from_docx(file_path)
        elif ext == ".doc":
            return extract_from_doc(file_path)
        return f"Unsupported file type: {ext}"
    except Exception as e:
        print(f"[ERROR] extract_text_from_file: {e}")
        return "Unable to extract text."


def extract_from_docx(file_path):
    try:
        from docx import Document

        doc = Document(file_path)
        return "\n".join(p.text for p in doc.paragraphs).strip()
    except Exception as e:
        print(f"[ERROR] extract_from_docx: {e}")
        return ""


def extract_from_doc(file_path):
    try:
        import mammoth

        with open(file_path, "rb") as doc_file:
            result = mammoth.extract_raw_text(doc_file)
            return result.value.strip()
    except Exception as e:
        print(f"[ERROR] extract_from_doc: {e}")
        return ""
