# 🧠 Opensource Decision Models — Streamlit Test UI

A modern Streamlit application for testing, benchmarking, and comparing **open-source decision models** running locally on **Ollama** via the `/v1/systemone` specification and the official TypeSafe SDK, featuring interactive Plotly visualizations, multiple execution backends, and a built-in simulation mode.

---

## 💡 What are Decision Models?

Decision models are a specialized category of AI models that **do not generate conversational prose**. Instead, they evaluate an input text or JSON payload ("state") against typed questions and return **deterministic, structured judgments with calibrated probabilities** in a single forward pass:

- **Single forward pass** — all questions evaluated simultaneously
- **Zero hallucinations** — answers strictly conform to defined schemas
- **Calibrated probabilities** — outputs reflect mathematical confidence per option
- **Ideal for automation** — ticket routing, content moderation, safety guardrails, policy enforcement, and intent classification

---

## 🤖 Supported Models & Platform Compatibility

> [!IMPORTANT]
> **Windows Users:** The `laya` model is built exclusively for Apple Silicon (MLX runtime) and will fail with `Error: this model requires MLX support` on Windows. For Windows and Linux, use **`tev1:0.8b`**, **`tev1` (4B)**, or **`nimble` (9B)**.

| Model | Size | Maker | Base Arch | OS Compatibility | Recommendation | Pull Command |
|-------|------|-------|-----------|------------------|----------------|--------------|
| **tev1:0.8b** | ~800 MB | Together AI | Qwen3.5 | Windows, Linux, macOS | ⚡ **Best for CPU / Laptops (Fastest)** | `ollama pull tev1:0.8b` |
| **tev1** | ~4.5 GB (4B) | Together AI | Qwen3.5 | Windows, Linux, macOS | 🎯 High accuracy | `ollama pull tev1` |
| **nimble** | ~5.5 GB (9B) | Bespoke Labs | Qwen3.5 | Windows, Linux, macOS | 🔬 Heavyweight classification | `ollama pull nimble` |
| **clef-flash** | ~5.5 GB (9B) | Cloudflare | Vision / Text | Windows, Linux, macOS | 🖼️ Multimodal | `ollama pull clef-flash` |
| **laya** | 846 MB | Convai Innovations | ModernBERT | **macOS Apple Silicon only** | 🍎 Mac MLX only | `ollama pull laya` |

---

## ⚡ Hardware & Latency Guide (CPU vs GPU)

Decision models run natively via Ollama on both CPU and GPU:

| Hardware | Recommended Model | Typical Latency | Notes |
|----------|-------------------|-----------------|-------|
| **CPU / Integrated GPU** (e.g. Intel Iris Xe) | **`tev1:0.8b`** | **~6–9 seconds** | 5x fewer parameters than 4B; 4x faster on CPU |
| **CPU / Integrated GPU** | `tev1` (4B) | ~30–40 seconds | Requires heavy CPU compute per token pass |
| **Dedicated GPU** (NVIDIA CUDA) | `tev1:0.8b` or `tev1` | **< 100 ms** | Ultra-fast parallelized tensor evaluation |
| **Any Hardware** | **🎭 Simulation Mode** | **< 20 ms** | Instant UI testing without model weights |

> [!TIP]
> **Warm Cache:** The first decision run on any model cold-loads the weights into memory. Subsequent runs are significantly faster because the app keeps the model warm in RAM with `keep_alive: "30m"`.

---

## 🚀 Quick Start

### 1. Activate Environment & Install Dependencies
```powershell
# Windows (PowerShell):
myvenv\Scripts\activate

# Install requirements:
pip install -r requirements.txt
```

### 2. Ensure Ollama is Running
```powershell
ollama serve
```

### 3. Pull a Decision Model (Windows Recommended)
For quick testing on CPU or Windows, pull the lightweight 0.8B variant:
```powershell
ollama pull tev1:0.8b
```
*(Or pull the full 4B model: `ollama pull tev1`)*

### 4. Launch the Streamlit App
```powershell
streamlit run app.py
```
Open your browser at **`http://localhost:8501`**.

---

## ✨ Features

- **⚡ Instant Demo / Simulation Mode:** Test all scenarios, question types, and visualizations immediately without waiting for model downloads.
- **🛠️ Visual Question Builder:** Interactively construct `choice`, `noul`, and `score` questions with full rubric configuration.
- **📁 Pre-built Scenarios:**
  - 💼 *Career & Role Decision* (role matching between AI Engineer / ML Engineer / Data Scientist, 90-day hiring probability, preparation check)
  - 📧 *Email Triage* (department routing, urgency score, churn risk, phishing detection)
  - 🛡️ *Content Moderation* (spam detection, toxicity grading, action recommendation)
  - 🎯 *Intent Routing* (support triage, sentiment score, escalation flag)
  - 🔧 *Tool-Call Safety* (agent safety guardrails and harm assessment)
  - 🔍 *Fact Verification* (evidence-based claim checking)
- **📊 Rich Interactive Visualizations:**
  - Horizontal probability bars with highlighted winner for `choice`
  - Calibrated probability gauges for `noul` (boolean judgments)
  - Rubric distribution charts with expected scores for `score`
- **🔀 Multi-Model Comparison:** Benchmark latency and compare decisions side-by-side across multiple models.
- **🔄 Dual Backends:** Run via raw HTTP `/v1/systemone` or official TypeSafe Python SDK (`typesafe-sdk`).
- **💾 JSON Export:** One-click download of full API request and response payloads.
- **🎨 Custom Dark Theme:** Curated glassmorphism design with responsive micro-animations.

---

## ❓ Question Types

| Type | Purpose | Returns | Example |
|------|---------|---------|---------|
| **`choice`** | Pick one discrete option from 2–26 choices | Chosen option + calibrated probability per option + confidence | Route ticket: billing, tech, or sales? |
| **`noul`** | Binary True/False judgment | Probability (0.0–1.0) that the condition is True | Is this content spam? |
| **`score`** | Place on an ordered rubric scale (e.g. 0 to 4) | Expected numerical score + probability per rubric level + confidence | Rate urgency: Low, Medium, High, Critical |

---

## 📡 API Reference

### 1. Via Raw HTTP (`/v1/systemone`)

```bash
curl http://localhost:11434/v1/systemone -d '{
  "model": "tev1:0.8b",
  "state": "Hi team, we were billed twice for March. Please refund or we cancel.",
  "questions": {
    "department": {
      "type": "choice",
      "instructions": "Which department should handle this email?",
      "criteria": {
        "billing": "Invoices, payments, refunds",
        "technical": "Bugs, outages, integrations",
        "sales": "Pricing, contracts, demos"
      }
    },
    "churn_risk": {
      "type": "noul",
      "instructions": "Does the customer threaten cancellation?"
    }
  }
}'
```

### 2. Via TypeSafe Python SDK (`typesafe-sdk`)

```python
from typesafe_sdk import TypeSafeClient, Choice, Noul, Score

client = TypeSafeClient(
    base_url="http://localhost:11434",
    api_key="ollama",  # Ollama accepts any non-empty string
)

response = client.systemone(
    model="tev1:0.8b",
    state="Hi team, we were billed twice for March. Please refund or we cancel.",
    questions={
        "department": Choice(
            instructions="Which department should handle this email?",
            criteria={
                "billing": "Invoices, payments, refunds",
                "technical": "Bugs, outages, integrations",
            },
        ),
        "churn_risk": Noul(
            instructions="Does the customer threaten cancellation?",
        ),
    },
)

print(response.answers.department.choice)       # "billing"
print(response.answers.churn_risk.noul)          # 0.84
```

---

## 📂 Project Structure

```
├── app.py                      # Main Streamlit application & layout
├── src/
│   ├── ollama_client.py        # Dual HTTP & TypeSafe SDK client + simulation engine
│   ├── question_builder.py     # Interactive visual question builder (Choice/Noul/Score)
│   ├── result_renderer.py      # Plotly probability charts, gauges, & JSON export
│   └── presets.py              # Pre-configured test scenarios (Career, Email, Moderation...)
├── assets/
│   └── style.css               # Modern dark theme styles & animations
├── requirements.txt            # Python dependencies
└── README.md                   # Project documentation & guides
```

---

## 📄 License

MIT
