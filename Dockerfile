FROM python:3.13.5-slim

WORKDIR /app

# Install Node.js and npm
RUN apt-get update && apt-get install -y nodejs npm

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install gemini-cli and set ownership of global npm modules to root
RUN npm install -g @google/gemini-cli && \
    chown -R root:root /usr/local/lib/node_modules /usr/local/bin /usr/local/share

COPY . .

CMD ["uvicorn", "gemini-rest:app", "--host", "0.0.0.0", "--port", "8000"]
