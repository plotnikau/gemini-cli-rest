
FROM python:3.13.5-slim

WORKDIR /app

# Install Node.js and npm
RUN apt-get update && apt-get install -y --no-install-recommends nodejs npm && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install gemini-cli
RUN npm install -g @google/gemini-cli

COPY . .

CMD ["uvicorn", "gemini-rest:app", "--host", "0.0.0.0", "--port", "8000"]
