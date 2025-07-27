from fastapi import FastAPI, Request
from pydantic import BaseModel
import subprocess

app = FastAPI()

class GeminiRequest(BaseModel):
    input: str

@app.post("/gemini")
async def gemini(request: GeminiRequest):
    input_text = request.input

    if not input_text:
        return {"error": "Missing input text"}, 400

    try:
        result = subprocess.run(
            ["gemini", "-y", "-p", input_text],
            capture_output=True,
            text=True,
            check=True
        )
        return {"output": result.stdout}
    except FileNotFoundError:
        return {"error": "gemini-cli command not found"}, 500
    except subprocess.CalledProcessError as e:
        return {"error": e.stderr}, 500

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)