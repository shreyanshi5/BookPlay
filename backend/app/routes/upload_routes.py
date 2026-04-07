from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse
from typing import Optional
import os
import uuid
from ..services.scene_splitter import split_into_scenes
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
    if not text and not file:
        raise HTTPException(status_code=400, detail="Either text or PDF file must be provided.")

    db = get_db()
    filename = None
    file_id = str(uuid.uuid4())

    # ---------------------------------------------------
    # Handle Input
    # ---------------------------------------------------
    if file:
        if not file.filename.lower().endswith(".pdf"):
            raise HTTPException(status_code=400, detail="Only PDF files are supported.")

        filename = f"{file_id}_{file.filename}"
        file_path = os.path.join(UPLOAD_DIR, filename)

        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)

        extracted_text = pdf_service.extract_text_from_pdf(file_path)
    else:
        extracted_text = text or ""
        file_path = None

    if not extracted_text.strip():
        raise HTTPException(status_code=400, detail="No extractable text found.")

    # ---------------------------------------------------
    # 🎬 Scene Splitting
    # ---------------------------------------------------
    cleaned_text = nlp_service.clean_text(extracted_text)
    scenes = split_into_scenes(cleaned_text)

    scene_outputs = []

    # ---------------------------------------------------
    # 🎤 Process Each Scene Separately
    # ---------------------------------------------------
    for scene_index, scene_text in enumerate(scenes, start=1):

        scene_segments = nlp_service.extract_dialogue_segments(scene_text)

        if not scene_segments:
            scene_segments = [{"speaker": "narrator", "text": scene_text}]

        # Ensure voices mapped per scene
        voice_mapping = voice_mapper.ensure_voice_mapping(
            db, [s["speaker"] for s in scene_segments]
        )

        # Generate scene audio file
        scene_output_id = str(uuid.uuid4())
        scene_filename = f"{scene_output_id}.mp3"
        scene_output_path = os.path.join(OUTPUT_DIR, scene_filename)

        tts_service.generate_narration_audio(
            segments=scene_segments,
            voice_mapping=voice_mapping,
            output_path=scene_output_path,
        )

        # Save output record
        db.execute(
            "INSERT INTO outputs (id, file_id, audio_path) VALUES (?, ?, ?)",
            (scene_output_id, file_id, scene_output_path),
        )

        scene_outputs.append({
            "scene_number": scene_index,
            "text": scene_text,
            "audio_url": f"/api/audio/{scene_output_id}"
        })

    # Save file record
    db.execute(
        "INSERT INTO files (id, filename) VALUES (?, ?)",
        (file_id, filename),
    )

    db.commit()
    return UploadResponse(
        id=file_id,
        scenes=scene_outputs,
        scene_count=len(scene_outputs)
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

