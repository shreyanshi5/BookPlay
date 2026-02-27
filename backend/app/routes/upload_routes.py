from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse
from typing import Optional
import os
import uuid

from ..models.schemas import UploadResponse, AudioResponse
from ..services import pdf_service, nlp_service, tts_service, voice_mapper
from ..database.db import get_db, init_db


router = APIRouter(tags=["audiobook"])


BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
OUTPUT_DIR = os.path.join(BASE_DIR, "outputs")


os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)


@router.on_event("startup")
def on_startup():
    """
    Initialize database on application startup.
    """
    init_db()


@router.post("/upload", response_model=UploadResponse)
async def upload_content(
    text: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
):
    """
    Accept raw text or a PDF file, process it, generate multi-voice narration,
    and return an identifier and audio URL.
    """
    if not text and not file:
        raise HTTPException(status_code=400, detail="Either text or PDF file must be provided.")

    # Persist uploaded file if provided
    db = get_db()
    filename = None
    file_id = str(uuid.uuid4())

    if file:
        if not file.filename.lower().endswith(".pdf"):
            raise HTTPException(status_code=400, detail="Only PDF files are supported.")

        filename = f"{file_id}_{file.filename}"
        file_path = os.path.join(UPLOAD_DIR, filename)
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)

        # Extract text from PDF
        extracted_text = pdf_service.extract_text_from_pdf(file_path)
    else:
        extracted_text = text or ""
        file_path = None

    if not extracted_text.strip():
        raise HTTPException(status_code=400, detail="No extractable text found.")

    # Clean and split text into dialogue segments
    cleaned_text = nlp_service.clean_text(extracted_text)
    segments = nlp_service.extract_dialogue_segments(cleaned_text)

    if not segments:
        # Fallback: treat the whole text as narrator if no dialogue detected
        segments = [{"speaker": "narrator", "text": cleaned_text}]

    # Ensure voices are mapped for all speakers
    voice_mapping = voice_mapper.ensure_voice_mapping(db, [s["speaker"] for s in segments])

    # Generate final audio file path
    output_id = str(uuid.uuid4())
    output_filename = f"{output_id}.mp3"
    output_path = os.path.join(OUTPUT_DIR, output_filename)

    # Generate and merge audio segments
    tts_service.generate_narration_audio(
        segments=segments,
        voice_mapping=voice_mapping,
        output_path=output_path,
    )

    # Record in database
    db.execute(
        """
        INSERT INTO files (id, filename)
        VALUES (?, ?)
        """,
        (file_id, filename),
    )

    db.execute(
        """
        INSERT INTO outputs (id, file_id, audio_path)
        VALUES (?, ?, ?)
        """,
        (output_id, file_id, output_path),
    )
    db.commit()

    return UploadResponse(
        id=output_id,
        audio_url=f"/api/audio/{output_id}",
    )


@router.get("/audio/{output_id}", response_model=AudioResponse)
async def get_audio(output_id: str):
    """
    Return the generated audio file for the given output identifier.
    """
    db = get_db()
    cursor = db.execute(
        "SELECT audio_path FROM outputs WHERE id = ?",
        (output_id,),
    )
    row = cursor.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Audio not found.")

    audio_path = row["audio_path"]
    if not os.path.exists(audio_path):
        raise HTTPException(status_code=404, detail="Audio file missing on server.")

    return FileResponse(audio_path, media_type="audio/mpeg", filename=os.path.basename(audio_path))

