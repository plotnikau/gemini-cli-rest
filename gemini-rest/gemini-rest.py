import os
import subprocess
from fastapi import FastAPI, Request, Depends, HTTPException, status, Header
from pydantic import BaseModel

# 1. Read the required service API key from an environment variable.
# This is the key your authorized user must provide.
SERVICE_API_KEY = os.getenv("SERVICE_API_KEY")

# 2. Create a dependency to verify the API key.
async def verify_api_key(x_api_key: str = Header(..., description="Your secret API key")):
    """
    Dependency to verify the X-API-Key header against the configured SERVICE_API_KEY.
    """
    if not SERVICE_API_KEY:
        # This is a server-side configuration error, so we return a 500.
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="API Key not configured on the server",
        )
    if x_api_key != SERVICE_API_KEY:
        # This is a client-side error for providing an invalid key.
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API Key"
        )

app = FastAPI()

class GeminiRequest(BaseModel):
    input: str

@app.post("/gemini", dependencies=[Depends(verify_api_key)])
async def gemini(request: GeminiRequest):
    input_text = request.input

    if not input_text:
        return {"error": "Missing input text"}, 400

    try:
        result = subprocess.run(
            ["gemini", "-m", "gemini-2.5-flash", "-p", input_text],
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