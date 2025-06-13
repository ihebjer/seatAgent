

## 📦 Project Structure

- `ingest.py` → Preprocess documents, split them into chunks, embed them, and store in vector DB (Chroma).
- `tcp_server.py` → Simulates real-time sensor data from a CSV file to the ML model.
- `ML_models.py` → Receives sensor data, predicts posture using a trained ML model, aggregates metadata, and triggers the LLM when needed.
- `run_localLLM.py` → Starts a Flask server running a local LLM with RAG and memory to handle posture-related queries.
- `query.py` → Allows manual user queries to be sent to the AI agent (e.g., questions about comfort, fatigue, posture recommendations).

---

## 🛠️ Step-by-Step Setup & Usage

### 1️⃣ Data Ingestion (RAG Setup)
Index the research documents.

```bash
python ingest.py
```

This will:
- Load source documents (PDFs, CSVs, etc.).
- Split them into context-friendly chunks.
- Generate embeddings using `Instructor-XL`.
- Store them into ChromaDB for semantic retrieval.

---

### 2️⃣ Start the AIO Sensor Simulator
Simulate real-time sensor streams using a TCP server (reads from a CSV file).

```bash
python tcp_server.py
```

This script:
- Reads sensor rows from your CSV.
- Streams them over a socket to the ML posture prediction module.

---

### 3️⃣ Run the Posture Aggregation + Trigger Engine
Start the posture prediction logic and metadata aggregation:

```bash
python ML_models.py
```

This:
- Connects to the TCP server.
- Predicts posture from incoming sensor data.
- Aggregates fatigue level, posture switches, and pressure analysis.
- Triggers the LLM when conditions are met (e.g., high fatigue).

---

### 4️⃣ Start the Local LLM API Server
Run the Flask server that loads the local LLM + RAG + conversational memory.

```bash
python run_localLLM.py
```

This:
- Loads the LLM and vector DB.
- Serves `/query` endpoint to respond to engineered and user queries.
- Maintains short-term memory between exchanges.

---

### 5️⃣ Send a Query to the Agent
Use the sample query tool to interact with the assistant:

```bash
python query.py
```

You can ask questions like:
- “What can I do to improve my posture?”
- “Suggest better seat adjustments based on my sitting pattern.”

---

## ✅ Requirements

Use `requirements.txt`

```bash
pip install -r requirements.txt
```

---


