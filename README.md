## AI Audiobook / Narration Backend

Backend service for generating multi‑voice audiobook / narration audio from raw text or PDF files.

### Tech Stack

- **FastAPI** (Python)
- **PyMuPDF** for PDF text extraction
- **spaCy** for NLP (NER, sentence parsing, simple dialogue attribution)
- **ElevenLabs API** for text‑to‑speech
- **SQLite** for simple persistence
- **Pydantic** for request/response schemas
- **pydub** for audio merging

### Project Structure

- **backend/**
  - **app/**
    - `main.py` – FastAPI app entrypoint
    - **routes/**
      - `upload_routes.py` – `/api/upload` and `/api/audio/{id}`
    - **services/**
      - `pdf_service.py` – PDF → text
      - `nlp_service.py` – cleanup + dialogue/speaker detection
      - `tts_service.py` – ElevenLabs TTS + audio merging
      - `voice_mapper.py` – character → voice mapping (SQLite‑backed)
    - **models/**
      - `schemas.py` – Pydantic models
    - **database/**
      - `db.py` – SQLite DB + tables
  - **uploads/** – stored uploaded PDFs
  - **outputs/** – generated `.mp3` files

### Setup

1. **Create and activate virtual environment (recommended)**

```bash
cd BookPlay
python -m venv .venv
.venv\Scripts\activate  # on Windows (PowerShell)
```

2. **Install dependencies**

```bash
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

3. **Set ElevenLabs API key**

Create a `.env` file in the project root or set an environment variable:

```bash
$env:ELEVENLABS_API_KEY = "YOUR_ELEVENLABS_API_KEY"  # PowerShell
```

You must also edit `backend/app/services/voice_mapper.py` and replace the placeholder `VOICE_ID_*` values in `PREDEFINED_VOICES` with your real ElevenLabs voice IDs.

### More expressive / emotional narration (recommended)

You can tune how expressive the narration is using these optional environment variables in `.env`:

```text
ELEVENLABS_MODEL_ID=eleven_v3
ELEVENLABS_OUTPUT_FORMAT=mp3_44100_128
```

- `ELEVENLABS_MODEL_ID`:
  - **`eleven_v3`** is the most expressive model (if your account has access).
  - Default is `eleven_multilingual_v2` if not set.
- `ELEVENLABS_OUTPUT_FORMAT` defaults to `mp3_44100_128`.

### Running the API

From the project root (`BookPlay`):

```bash
uvicorn backend.app.main:app --reload
```

The API will be available at `http://localhost:8000`. Interactive docs:

- Swagger UI: `http://localhost:8000/docs`

### Main Endpoints

- **POST** `/api/upload`
  - **Form fields**:
    - `text` (optional) – raw text
    - `file` (optional) – PDF file (`multipart/form-data`, `.pdf` only)
  - At least one of `text` or `file` must be provided.
  - Returns JSON:
    - `id` – output identifier
    - `audio_url` – URL to download the generated audio, e.g. `/api/audio/{id}`

- **GET** `/api/audio/{id}`
  - Streams the generated `.mp3` file for the given `id`.

### Notes

- Dialogue detection is heuristic: it looks for text inside quotes (`"..."`) and uses spaCy NER plus simple patterns (e.g. `"Hello," said John.`) to attribute speech to PERSON entities; all other text defaults to the `narrator`.
- Character → voice assignments are persisted in the `characters` table, so the same character keeps the same voice across uploads.

