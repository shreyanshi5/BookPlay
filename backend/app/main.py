from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

from .routes.upload_routes import router as upload_router


def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application instance.
    """
    app = FastAPI(title="AI Audiobook/Narration Backend")

    # Allow all origins for simplicity; tighten in production
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register routers
    app.include_router(upload_router, prefix="/api")

    return app


app = create_app()


@app.get("/", response_class=HTMLResponse)
async def index():
    """
    Simple HTML UI for uploading text or a PDF.
    """
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8" />
        <title>AI Audiobook Generator</title>
        <style>
            body { font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
                   max-width: 800px; margin: 40px auto; padding: 0 16px; background: #0f172a; color: #e5e7eb; }
            h1 { font-size: 2rem; margin-bottom: 0.5rem; }
            p { color: #cbd5f5; }
            .card { background: #020617; border-radius: 12px; padding: 24px; box-shadow: 0 10px 40px rgba(15,23,42,0.7); }
            label { display: block; margin-top: 16px; font-weight: 600; }
            textarea { width: 100%; min-height: 140px; margin-top: 8px; padding: 10px;
                       border-radius: 8px; border: 1px solid #1f2937; background: #020617; color: #e5e7eb; }
            input[type="file"] { margin-top: 8px; }
            button { margin-top: 20px; padding: 10px 18px; border-radius: 999px;
                     border: none; background: linear-gradient(to right, #4f46e5, #ec4899);
                     color: white; font-weight: 600; cursor: pointer; }
            button:disabled { opacity: .6; cursor: wait; }
            .note { font-size: 0.85rem; color: #9ca3af; margin-top: 4px; }
            .result { margin-top: 24px; padding: 12px 16px; border-radius: 8px; background: #020617; border: 1px solid #1f2937; }
            a { color: #60a5fa; }
            audio { width: 100%; margin-top: 12px; }
        </style>
    </head>
    <body>
        <h1>AI Audiobook Generator</h1>
        <p>Write text or upload a PDF, then get a multi‑voice narration.</p>
        <div class="card">
            <form id="uploadForm">
                <label for="text">Text (optional)</label>
                <textarea id="text" name="text" placeholder='"Hello," said John. "Hi," replied Mary.'></textarea>

                <label for="file">PDF file</label>
                <input id="file" name="file" type="file" accept="application/pdf" />
                <div class="note">You can use either text, a PDF, or both.</div>

                <button id="submitBtn" type="button">Generate Audio</button>
            </form>
            <div id="result" class="result" style="display:none;">
                <div id="resultMessage"></div>
                <audio id="audioPlayer" controls style="display:none;"></audio>
                <div id="downloadLink" class="note" style="display:none;"></div>
            </div>
        </div>

        <script>
            const submitBtn = document.getElementById("submitBtn");
            const resultDiv = document.getElementById("result");

            submitBtn.addEventListener("click", async () => {

                resultDiv.innerHTML = "";
                resultDiv.style.display = "none";
                submitBtn.disabled = true;
                submitBtn.textContent = "Generating...";

                try {
                    const formData = new FormData();
                    const textVal = document.getElementById("text").value;
                    const fileInput = document.getElementById("file");

                    if (textVal.trim()) {
                        formData.append("text", textVal);
                    }

                    if (fileInput.files.length > 0) {
                        formData.append("file", fileInput.files[0]);
                    }

                    if (!formData.has("text") && !formData.has("file")) {
                        alert("Please enter some text or choose a PDF file.");
                        submitBtn.disabled = false;
                        submitBtn.textContent = "Generate Audio";
                        return;
                    }

                    const resp = await fetch("/api/upload", {
                        method: "POST",
                        body: formData,
                    });

                    if (!resp.ok) {
                        const err = await resp.json().catch(() => ({}));
                        throw new Error(err.detail || "Failed to generate audio");
                    }

                    const data = await resp.json();

                    // -----------------------------
                    // 🎬 Render Scene Audio Players
                    // -----------------------------

                    resultDiv.style.display = "block";

                    const header = document.createElement("h2");
                    header.textContent = "Generated Scenes";
                    resultDiv.appendChild(header);

                    data.scenes.forEach(scene => {

                        const container = document.createElement("div");
                        container.style.marginTop = "20px";
                        container.style.padding = "15px";
                        container.style.border = "1px solid #1f2937";
                        container.style.borderRadius = "10px";
                        container.style.background = "#0f172a";

                        const title = document.createElement("h3");
                        title.textContent = `Scene ${scene.scene_number}`;

                        const audio = document.createElement("audio");
                        audio.controls = true;
                        audio.src = scene.audio_url;
                        audio.style.marginTop = "10px";
                        audio.style.width = "100%";

                        container.appendChild(title);
                        container.appendChild(audio);

                        resultDiv.appendChild(container);
                    });

                } catch (err) {
                    resultDiv.style.display = "block";
                    resultDiv.innerHTML = "<strong>Error:</strong> " + err.message;
                } finally {
                    submitBtn.disabled = false;
                    submitBtn.textContent = "Generate Audio";
                }
            });
        </script>
    </body>
    </html>
    """


@app.get("/health")
async def health_check():
    """
    Simple health check endpoint to verify that the API is running.
    """
    return {"status": "ok"}

