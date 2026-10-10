"""
Ollama client for /v1/systemone decision model endpoint
and optional TypeSafe Python SDK integration.
"""

import math
import random
import re
import time
import requests
from typing import Any


OLLAMA_BASE_URL = "http://localhost:11434"

# Known decision model families on Ollama
DECISION_MODEL_FAMILIES = {"tev1", "nimble", "clef-flash", "clef", "laya"}


def check_connection(base_url: str = OLLAMA_BASE_URL) -> bool:
    """Ping Ollama to verify it's running."""
    try:
        resp = requests.get(f"{base_url}/", timeout=3)
        return resp.status_code == 200
    except Exception:
        return False


def list_local_models(base_url: str = OLLAMA_BASE_URL) -> list[dict]:
    """
    GET /api/tags → list all locally pulled models.
    """
    try:
        resp = requests.get(f"{base_url}/api/tags", timeout=10)
        resp.raise_for_status()
        return resp.json().get("models", [])
    except Exception:
        return []


def get_decision_models(base_url: str = OLLAMA_BASE_URL) -> list[dict]:
    """Return only models whose family matches a known decision model."""
    all_models = list_local_models(base_url)
    decision_models = []
    for m in all_models:
        name = m.get("name", "").lower()
        family = name.split(":")[0]
        if family in DECISION_MODEL_FAMILIES:
            decision_models.append(m)
    return decision_models


def pull_model(model_name: str, base_url: str = OLLAMA_BASE_URL) -> dict:
    """
    Trigger Ollama to pull a model via POST /api/pull.
    Returns status dict.
    """
    resp = requests.post(
        f"{base_url}/api/pull",
        json={"name": model_name, "stream": False},
        timeout=1800,
    )
    resp.raise_for_status()
    return resp.json()


def run_decision(
    model: str,
    state: Any,
    questions: dict,
    base_url: str = OLLAMA_BASE_URL,
) -> dict:
    """
    POST /v1/systemone — send a decision request.

    Args:
        model: Ollama model name (e.g. "tev1:0.8b", "tev1", "nimble")
        state: The text or JSON object to judge
        questions: Dict of named questions, each with type/instructions/criteria
        base_url: Ollama server URL

    Returns:
        dict with keys: model, answers, usage, _latency_ms
    """
    payload = {
        "model": model,
        "state": state,
        "questions": questions,
        "keep_alive": "30m",
    }


    start = time.perf_counter()
    resp = requests.post(
        f"{base_url}/v1/systemone",
        json=payload,
        timeout=120,
    )
    elapsed_ms = (time.perf_counter() - start) * 1000

    resp.raise_for_status()
    result = resp.json()
    result["_latency_ms"] = round(elapsed_ms, 1)
    return result


def is_typesafe_available() -> bool:
    """Check if typesafe_sdk is installed in current python environment."""
    try:
        import typesafe_sdk  # noqa: F401
        return True
    except ImportError:
        return False


def run_decision_typesafe(
    model: str,
    state: Any,
    questions: dict,
    base_url: str = OLLAMA_BASE_URL,
) -> dict:
    """
    Send decision request via TypeSafe's official Python SDK.
    """
    import os
    from typesafe_sdk import TypeSafeClient, Choice, Noul, Score

    os.environ["TYPESAFE_BASE_URL"] = base_url
    os.environ["TYPESAFE_API_KEY"] = "ollama"

    start = time.perf_counter()
    with TypeSafeClient() as client:
        sdk_questions = {}
        for q_name, q_data in questions.items():
            q_type = q_data.get("type", "choice")
            instructions = q_data.get("instructions", "")
            criteria = q_data.get("criteria")

            if q_type == "choice":
                sdk_questions[q_name] = Choice(instructions=instructions, criteria=criteria or {})
            elif q_type == "noul":
                sdk_questions[q_name] = Noul(instructions=instructions, criteria=criteria)
            elif q_type == "score":
                sdk_questions[q_name] = Score(instructions=instructions, criteria=criteria or [])

        resp = client.systemone(
            model=model,
            state=state,
            questions=sdk_questions,
        )

    elapsed_ms = (time.perf_counter() - start) * 1000

    answers = {}
    for q_name in questions:
        ans_obj = getattr(resp.answers, q_name, None) if hasattr(resp, "answers") else None
        if ans_obj is not None:
            if hasattr(ans_obj, "choice"):
                answers[q_name] = {
                    "type": "choice",
                    "choice": ans_obj.choice,
                    "probabilities": getattr(ans_obj, "probabilities", {}),
                    "confidence": getattr(ans_obj, "confidence", 1.0),
                }
            elif hasattr(ans_obj, "noul"):
                answers[q_name] = {
                    "type": "noul",
                    "noul": ans_obj.noul,
                }
            elif hasattr(ans_obj, "score"):
                answers[q_name] = {
                    "type": "score",
                    "score": ans_obj.score,
                    "legend": getattr(ans_obj, "legend", {}),
                    "probabilities": getattr(ans_obj, "probabilities", {}),
                    "confidence": getattr(ans_obj, "confidence", 1.0),
                }

    return {
        "model": model,
        "answers": answers,
        "usage": getattr(resp, "usage", {"input_tokens": 0, "output_tokens": 0}),
        "_latency_ms": round(elapsed_ms, 1),
    }


def simulate_decision(
    model: str,
    state: Any,
    questions: dict,
) -> dict:
    """
    Deterministic/heuristic simulation of a decision model's output.
    Useful for testing the UI, scenarios, and visualizations without downloading models.
    """
    state_str = str(state).lower()
    answers = {}

    for q_name, q_data in questions.items():
        q_type = q_data.get("type", "choice")
        instructions = q_data.get("instructions", "").lower()
        criteria = q_data.get("criteria")

        if q_type == "choice":
            crit_dict = criteria if isinstance(criteria, dict) else {"option_1": "", "option_2": ""}
            scores = {}
            for opt, desc in crit_dict.items():
                opt_lower = str(opt).lower()
                desc_lower = str(desc or "").lower()
                score = 1.0
                # keyword matching in state
                words = re.findall(r"\w+", f"{opt_lower} {desc_lower}")
                for w in words:
                    if len(w) > 3 and w in state_str:
                        score += 3.5
                scores[opt] = score

            # Softmax
            exp_scores = {k: math.exp(v) for k, v in scores.items()}
            total_exp = sum(exp_scores.values()) or 1.0
            probs = {k: round(v / total_exp, 4) for k, v in exp_scores.items()}
            best_opt = max(probs.keys(), key=lambda k: probs[k])

            answers[q_name] = {
                "type": "choice",
                "choice": best_opt,
                "probabilities": probs,
                "confidence": probs[best_opt],
            }

        elif q_type == "noul":
            # Heuristic detection of affirmative intent in state
            true_keywords = [
                "spam", "free", "money", "claim", "$", "prize", "refund",
                "cancel", "terminate", "phishing", "threaten", "urgent",
                "risk", "error", "401", "immediately", "block"
            ]
            hits = sum(1 for kw in true_keywords if kw in state_str and kw in instructions)
            base_prob = 0.88 if hits > 0 else (0.12 if "not" in instructions else 0.45)
            # Add slight jitter based on hash
            jitter = (hash(q_name + state_str) % 15 - 7) / 100.0
            p = max(0.01, min(0.99, base_prob + jitter))

            answers[q_name] = {
                "type": "noul",
                "noul": round(p, 3),
            }

        elif q_type == "score":
            levels = criteria if isinstance(criteria, list) else ["Low", "Medium", "High"]
            n = len(levels)
            # Distribute probability mass with peak depending on text urgency
            peak = 0
            if any(w in state_str for w in ["cancel", "critical", "severe", "urgent", "toxic", "refund"]):
                peak = n - 1
            elif any(w in state_str for w in ["mild", "medium", "moderate", "review"]):
                peak = min(1, n - 1)

            weights = []
            for i in range(n):
                dist = abs(i - peak)
                weights.append(math.exp(-dist * 1.8))
            total_w = sum(weights) or 1.0
            probs = {str(i): round(w / total_w, 4) for i, w in enumerate(weights)}
            expected = sum(i * probs[str(i)] for i in range(n))
            legend = {str(i): lvl for i, lvl in enumerate(levels)}

            answers[q_name] = {
                "type": "score",
                "score": round(expected, 2),
                "legend": legend,
                "probabilities": probs,
                "confidence": round(max(probs.values()), 2),
            }

    # Simulate realistic sub-second latency (10-35ms)
    sim_latency = round(random.uniform(11.2, 32.5), 1)

    return {
        "model": f"{model} (Simulated)",
        "answers": answers,
        "usage": {
            "input_tokens": max(15, len(state_str.split())),
            "output_tokens": len(questions) * 4,
        },
        "_latency_ms": sim_latency,
        "_simulated": True,
    }


# ── Model metadata for the UI ─────────────────────────────────────────────

MODEL_INFO = {
    "tev1:0.8b": {
        "name": "Tev1 (0.8B)",
        "maker": "Together AI",
        "size": "0.8B (~600MB)",
        "description": "Ultra-lightweight fast decision model fine-tuned from Qwen3.5. Excellent for quick local testing on any machine.",
        "capabilities": ["decision", "tools", "thinking"],
        "context_window": 4096,
        "platform": "Windows, Linux, macOS (Recommended for Windows)",
    },
    "tev1": {
        "name": "Tev1 (4B)",
        "maker": "Together AI",
        "size": "4B (~2.5GB)",
        "description": "Flagship open-source decision model from Together AI, fine-tuned from Qwen3.5. Highly accurate classification.",
        "capabilities": ["decision", "tools", "thinking"],
        "context_window": 4096,
        "platform": "Windows, Linux, macOS",
    },
    "nimble": {
        "name": "Nimble",
        "maker": "Bespoke Labs",
        "size": "9B (~5.5GB)",
        "description": "Fast typed classification decision model fine-tuned from Qwen3.5-9B.",
        "capabilities": ["decision", "tools", "thinking"],
        "context_window": 4096,
        "platform": "Windows, Linux, macOS",
    },
    "laya": {
        "name": "Laya",
        "maker": "Convai Innovations",
        "size": "421M (846MB)",
        "description": "Ultra-fast decision model fine-tuned from ModernBERT-large. Single-question latency < 10ms.",
        "capabilities": ["decision"],
        "context_window": 512,
        "platform": "macOS only (Requires Apple Silicon MLX)",
    },
    "clef-flash": {
        "name": "Clef-Flash",
        "maker": "Cloudflare",
        "size": "9B",
        "description": "Multimodal decision model — processes text, JSON, or images.",
        "capabilities": ["decision", "vision"],
        "context_window": 4096,
        "platform": "Windows, Linux, macOS",
    },
    "clef": {
        "name": "Clef",
        "maker": "Cloudflare",
        "size": "27B",
        "description": "High-accuracy multimodal decision model for complex judgments.",
        "capabilities": ["decision", "vision"],
        "context_window": 4096,
        "platform": "Windows, Linux, macOS",
    },
}


def get_model_info(model_name: str) -> dict:
    """Get metadata for a model by its tag or family name."""
    clean_name = model_name.lower().strip()
    if clean_name in MODEL_INFO:
        return MODEL_INFO[clean_name]

    family = clean_name.split(":")[0]
    if family in MODEL_INFO:
        return MODEL_INFO[family]

    return {
        "name": clean_name.title(),
        "maker": "Local Model",
        "size": "Unknown",
        "description": "Local Ollama model",
        "capabilities": ["decision"],
        "context_window": 2048,
        "platform": "Local Ollama",
    }
