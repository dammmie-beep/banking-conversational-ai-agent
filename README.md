# Bank Conversational AI Agent

A fully offline conversational AI agent built for Bank customer service. Built with Flask, llama.cpp, and a small embedding model — no internet connection required after initial setup.

---

## Features

- **Product Queries** — Answer questions about Bank products (loans, savings, investments, debit cards)
- **Account Queries** — Retrieve customer account details and transaction history
- **ATM Card Blocking** — Full multi-turn card blocking flow with support for multiple cards per account
- **Sliding Window Memory** — Maintains conversation context across multiple turns per session
- **Fully Offline** — Runs entirely on local hardware after one-time model download

---

## Tech Stack

| Component | Technology |
|---|---|
| API Framework | Flask |
| LLM | SmolLM2 1.7B Instruct (GGUF Q4_K_M) via llama.cpp |
| Embedding Model | sentence-transformers/all-MiniLM-L6-v2 |
| Vector Store | FAISS (CPU) |
| Data Source | Excel (.xlsx) via pandas |
| Runtime | Python 3.8+ |

---

## Project Structure

```
banking_agent/
│
├── models/
│   ├── smollm2-1.7b-instruct-q4_k_m.gguf   # LLM model
│   └── minilm/                               # Embedding model (cached)
│
├── data/
│   ├── banking_data.xlsx                     # Customer, Transaction, Card sheets
│   └── products.txt                          # Product information
│
├── app/
│   ├── __init__.py                           # Flask app factory
│   ├── agent.py                              # Core agent + intent routing
│   ├── llm.py                                # llama.cpp wrapper
│   ├── embeddings.py                         # FAISS vector store
│   ├── data_loader.py                        # Excel data ingestion
│   ├── tools.py                              # Tool execution handlers
│   ├── memory.py                             # Sliding window memory
│   ├── routes.py                             # Flask API routes
│   └── intent_router.py                      # Intent detection
│
├── requirements.txt
├── config.py                                 # All configuration
├── run.py                                    # Entry point
└── agent.log                                 # Runtime logs (auto-generated)
```

---

## Requirements

- Python 3.8 or higher
- 4GB+ RAM recommended
- Windows / Linux / macOS

---

## Installation

### Step 1 — Clone the repository
```bash
git clone https://github.com/dammmie-beep/banking-conversational-ai-agent.git
cd banking-agent
```

### Step 2 — Create and activate virtual environment
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Mac/Linux
source venv/bin/activate
```

### Step 3 — Install dependencies
```bash
pip install flask openpyxl pandas faiss-cpu sentence-transformers python-dotenv numpy

# Windows (CPU only)
pip install llama-cpp-python --force-reinstall --no-cache-dir

# Linux/Mac with OpenBLAS acceleration
CMAKE_ARGS="-DLLAMA_BLAS=ON -DLLAMA_BLAS_VENDOR=OpenBLAS" \
  pip install llama-cpp-python --force-reinstall --no-cache-dir
```

### Step 4 — Download the LLM model (one time, requires internet)
```bash
huggingface-cli download HuggingFaceTB/SmolLM2-1.7B-Instruct-GGUF \
  smollm2-1.7b-instruct-q4_k_m.gguf \
  --local-dir ./models
```

### Step 5 — Cache the embedding model (one time, requires internet)
```bash
python -c "
from sentence_transformers import SentenceTransformer
model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
model.save('./models/minilm')
print('Embedding model cached.')
"
```

### Step 6 — Add your data files
Place the following files in the `data/` folder:
- `banking_data.xlsx` — Excel file with sheets: `Customer`, `Transaction`, `Card`
- `products.txt` — Plain text product information

### Step 7 — Run the server
```bash
python run.py
```

The server starts at `http://127.0.0.1:5000`

---

## API Endpoints

### Health Check
```
GET /api/health
```
Response:
```json
{
  "status": "ok",
  "message": "Banking Agent is running."
}
```

---

### Chat
```
POST /api/chat
Content-Type: application/json
```
Request:
```json
{
  "session_id": "user-session-1",
  "message": "What savings accounts do you offer?"
}
```
Response:
```json
{
  "session_id": "user-session-1",
  "response": "Globus Bank offers several savings options including..."
}
```

> **Note:** Use the same `session_id` across multiple requests to maintain conversation context.

---

### View Conversation History
```
GET /api/session/{session_id}/history
```

---

### Clear Session
```
DELETE /api/session/{session_id}/clear
```

---

## Excel Data Format

The `banking_data.xlsx` file must contain three sheets:

**Customer sheet:**
| Account_No | Name | Balance | ... |
|---|---|---|---|

**Transaction sheet:**
| Account_No | Transaction_Date | Amount | Description | ... |
|---|---|---|---|

**Card sheet:**
| Account_No | Card_Issuer | Card_Type | Status | Card_Activation_Date |
|---|---|---|---|---|

> Date format: `DD/MM/YYYY HH:MM:SS`

---

## How It Works

```
User Message (Postman/API)
        │
        ▼
   Flask Route (/api/chat)
        │
        ▼
   Intent Router
   ├── "block_card"    → handle_block_card()   [pure Python, no LLM]
   ├── "account_query" → handle_account_query() [tool + LLM summary]
   ├── "product_query" → handle_product_query() [RAG + LLM]
   └── "general"       → handle_general()       [LLM]
        │
        ▼
   Session Memory (Sliding Window, 10 turns)
        │
        ▼
   Response → User
```

### Card Blocking Flow
```
1. User requests card block
2. Agent asks for account number (if not provided)
3. Agent fetches all linked cards
4. If one card → asks for confirmation → blocks
5. If multiple cards → lists them → asks which one → confirms → blocks
```

---

## Configuration

All settings are in `config.py`:

```python
N_CTX = 4096       # LLM context window
N_THREADS = 4       # CPU threads (set to your CPU core count)
MAX_TOKENS = 512    # Maximum response length
TEMPERATURE = 0.2  # Lower = more deterministic
N_BATCH = 64        # Batch size for inference
WINDOW_SIZE = 10   # Conversation turns to retain
```

---

## Testing with Postman

1. Open Postman
2. Set method to `POST`
3. URL: `http://127.0.0.1:5000/api/chat`
4. Headers: `Content-Type: application/json`
5. Body: `raw` → `JSON`
6. Send messages keeping the same `session_id` for multi-turn conversations

---

## Offline Usage

After completing the installation steps above, the system runs fully offline:
- LLM model is stored in `./models/`
- Embedding model is stored in `./models/minilm/`
- All data is loaded from local Excel and text files
- No API calls, no internet dependency at runtime

---

## Known Limitations

- Response time: 20–60 seconds per message on CPU-only machines (no GPU)
- SmolLM2 1.7B is a small model — complex reasoning may occasionally be imprecise
- Card blocking uses in-memory state; changes reset on server restart (no persistent DB)

---

## License

This project was built as part of a technical assessment for Globus Bank.