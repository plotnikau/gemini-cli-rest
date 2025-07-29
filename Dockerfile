FROM python:3.13.5-slim

WORKDIR /app

# Install Node.js and npm
RUN apt-get update && \
    apt-get install -y curl && \
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y nodejs && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install gemini-cli and set ownership of global npm modules to root
RUN npm install -g @google/gemini-cli 

COPY . .

CMD ["uvicorn", "gemini-rest:app", "--host", "0.0.0.0", "--port", "8000"]
