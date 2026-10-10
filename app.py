"""
🧠 Opensource Decision Models — Streamlit Test UI

Test and compare decision models running on Ollama
via the /v1/systemone endpoint (TypeSafe Jev API) or TypeSafe SDK,
with built-in Simulation/Demo mode for instant testing.
"""

import json
import streamlit as st

from src.ollama_client import (
    check_connection,
    list_local_models,
    get_decision_models,
    get_model_info,
    run_decision,
    run_decision_typesafe,
    simulate_decision,
    is_typesafe_available,
    pull_model,
    OLLAMA_BASE_URL,
    MODEL_INFO,
)
from src.question_builder import (
    render_question_builder,
    load_questions_from_preset,
    get_state_input,
)
from src.result_renderer import render_results, render_comparison
from src.presets import PRESETS


# ── Page config ────────────────────────────────────────────────────
st.set_page_config(
    page_title="Decision Models Tester",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Load custom CSS ────────────────────────────────────────────────
try:
    with open("assets/style.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
except Exception:
    pass


# ── Session state defaults ─────────────────────────────────────────
if "history" not in st.session_state:
    st.session_state.history = []
if "compare_mode" not in st.session_state:
    st.session_state.compare_mode = False
if "last_result" not in st.session_state:
    st.session_state.last_result = None
if "selected_preset" not in st.session_state:
    st.session_state.selected_preset = None
if "demo_mode" not in st.session_state:
    st.session_state.demo_mode = False
if "execution_engine" not in st.session_state:
    st.session_state.execution_engine = "HTTP (/v1/systemone)"


# ── Cached helpers for snappy UI ──────────────────────────────────
@st.cache_data(ttl=15, show_spinner=False)
def get_cached_connection():
    return check_connection()

@st.cache_data(ttl=30, show_spinner=False)
def get_cached_models():
    if not get_cached_connection():
        return [], []
    return get_decision_models(), list_local_models()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  SIDEBAR
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

with st.sidebar:
    st.markdown("# 🧠 Decision Models")
    st.caption("Test Ollama decision models via `/v1/systemone`")

    st.divider()

    # ── Connection status ──────────────────────────────────────────
    connected = get_cached_connection()
    if connected:
        st.markdown(
            '<div class="status-connected">'
            '<span class="pulse-dot connected"></span> Ollama Connected'
            '</div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<div class="status-disconnected">'
            '<span class="pulse-dot disconnected"></span> Ollama Offline'
            '</div>',
            unsafe_allow_html=True,
        )
        st.caption("Run `ollama serve` or use Demo Mode to test offline.")

    st.divider()

    # ── Model selection ────────────────────────────────────────────
    st.markdown("### 🤖 Models")
    decision_models, all_local = get_cached_models() if connected else ([], [])

    has_decision_models = len(decision_models) > 0


    # Engine / Mode selector
    engine_options = []
    if has_decision_models:
        engine_options.append("HTTP (/v1/systemone)")
        if is_typesafe_available():
            engine_options.append("TypeSafe SDK")
        engine_options.append("🎭 Simulation / Demo Mode")
    else:
        engine_options.append("🎭 Simulation / Demo Mode")
        if connected and all_local:
            engine_options.append("Live Model (Ollama /v1/systemone)")
            if is_typesafe_available():
                engine_options.append("TypeSafe SDK")

    chosen_engine = st.selectbox(
        "Execution Engine",
        engine_options,
        index=0,
        help="Choose between live Ollama execution, TypeSafe SDK, or instant simulation mode",
    )
    is_simulation = "Simulation" in chosen_engine

    # Notice when no decision models are installed
    if not has_decision_models:
        st.info(
            "💡 **No decision models installed yet**\n\n"
            "Running in **Simulation Mode** so you can test all scenarios immediately!\n\n"
            "**Windows-ready models to pull:**\n"
            "- `tev1:0.8b` *(~600MB — fast)*\n"
            "- `tev1` *(4B, Together AI)*\n"
            "- `nimble` *(9B, Bespoke Labs)*\n\n"
            "*(Note: `laya` requires macOS Apple Silicon MLX)*"
        )

    # Model list definition
    if is_simulation:
        available_model_names = ["tev1:0.8b", "tev1", "nimble", "clef-flash"]
    elif has_decision_models:
        available_model_names = [m["name"] for m in decision_models]
    else:
        available_model_names = [m["name"] for m in all_local] if all_local else ["tev1:0.8b"]

    # Compare mode toggle
    st.session_state.compare_mode = st.toggle(
        "🔀 Compare mode",
        value=st.session_state.compare_mode,
        help="Send the same request to multiple models and compare decisions side-by-side",
    )

    if st.session_state.compare_mode:
        selected_models = st.multiselect(
            "Select models to compare",
            available_model_names,
            default=available_model_names[:2] if len(available_model_names) >= 2 else available_model_names,
        )
    else:
        selected_model = st.selectbox(
            "Select model",
            available_model_names,
            index=0,
        )
        selected_models = [selected_model] if selected_model else []

    # Show model info cards
    for model_name in selected_models:
        info = get_model_info(model_name)
        caps_html = " ".join(
            f'<span class="model-badge badge-{c}">{c}</span>'
            for c in info.get("capabilities", [])
        )
        plat_color = "#10B981" if "Windows" in info.get("platform", "") else ("#EF4444" if "macOS only" in info.get("platform", "") else "#94A3B8")
        st.markdown(
            f'<div class="model-card">'
            f'<strong>{info["name"]}</strong> '
            f'<span style="color: #94A3B8; font-size: 0.8rem;">{info["size"]}</span><br>'
            f'<span style="color: #64748B; font-size: 0.8rem;">{info["maker"]}</span><br>'
            f'<span style="color: {plat_color}; font-size: 0.75rem;">🖥️ {info.get("platform", "Local")}</span><br>'
            f'<div style="margin-top: 6px;">{caps_html}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    # ── Model puller expander ──────────────────────────────────────
    if connected:
        with st.expander("📥 Pull Decision Model"):
            model_to_pull = st.selectbox(
                "Select model to pull",
                ["tev1:0.8b", "tev1", "nimble"],
                index=0,
                help="tev1:0.8b is recommended for fast downloads on Windows",
            )
            if st.button("Download to Ollama", use_container_width=True):
                with st.spinner(f"Pulling {model_to_pull}... (this may take a few minutes)"):
                    try:
                        pull_model(model_to_pull)
                        st.success(f"✅ Successfully pulled `{model_to_pull}`!")
                        st.rerun()
                    except Exception as err:
                        st.error(f"Pull error: {err}")

    st.divider()

    # ── Presets ────────────────────────────────────────────────────
    st.markdown("### 📁 Scenarios")
    preset_names = list(PRESETS.keys())
    chosen_preset = st.radio(
        "Load a scenario",
        preset_names,
        index=None,
        label_visibility="collapsed",
    )

    if chosen_preset and chosen_preset != st.session_state.selected_preset:
        st.session_state.selected_preset = chosen_preset
        preset = PRESETS[chosen_preset]
        load_questions_from_preset(preset["questions"])
        if isinstance(preset["state"], dict):
            st.session_state["state_json"] = json.dumps(preset["state"], indent=2)
            st.session_state["state_mode"] = "JSON"
        else:
            st.session_state["state_text"] = preset["state"]
            st.session_state["state_mode"] = "Plain text"
        st.rerun()

    st.divider()

    # ── History ────────────────────────────────────────────────────
    st.markdown("### 📜 History")
    if st.session_state.history:
        for i, entry in enumerate(reversed(st.session_state.history[-10:])):
            idx = len(st.session_state.history) - 1 - i
            model = entry.get("model", "?")
            latency = entry.get("result", {}).get("_latency_ms", 0)
            n_questions = len(entry.get("questions", {}))
            if st.button(
                f"#{idx + 1}  {model}  ·  {n_questions}q  ·  {latency:.0f}ms",
                key=f"hist_{idx}",
                use_container_width=True,
            ):
                st.session_state.last_result = entry
    else:
        st.caption("No decisions yet. Run one to see history.")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  MAIN AREA
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

st.markdown("# 🧠 Opensource Decision Models Tester")
st.markdown(
    "Test, evaluate, and benchmark open-source decision models using the `/v1/systemone` specification. "
    "Decision models produce fast, deterministic typed answers (Choice, Noul, Score) in a single forward pass."
)

if is_simulation:
    st.warning("⚡ **Demo / Simulation Mode Active:** Outputs are generated via the built-in deterministic decision engine for instant testing.")

# ── State input ────────────────────────────────────────────────────
st.markdown("## 📝 State")
st.caption("The text or JSON object that the decision model evaluates.")
state_value = get_state_input()

st.divider()

# ── Question builder ──────────────────────────────────────────────
st.markdown("## ❓ Questions")
st.caption("Define 1–64 typed questions. Each question is evaluated simultaneously in a single forward pass.")
questions = render_question_builder()

st.divider()

# ── Request preview ───────────────────────────────────────────────
with st.expander("📋 Request Preview (JSON)"):
    preview = {
        "engine": chosen_engine,
        "model": selected_models[0] if selected_models else "—",
        "state": state_value,
        "questions": questions,
    }
    st.code(json.dumps(preview, indent=2, default=str), language="json")

# ── Run button & Validation ───────────────────────────────────────
has_valid_state = bool(
    state_value is not None
    and ((isinstance(state_value, str) and state_value.strip()) or isinstance(state_value, (dict, list)))
)
has_questions = len(questions) > 0
has_models = len(selected_models) > 0

if not has_valid_state:
    w_col1, w_col2 = st.columns([3, 2])
    with w_col1:
        st.warning("⚠️ **State is empty:** Scroll up to **📝 State** to enter your context/background before running.")
    with w_col2:
        if st.button("💡 Auto-fill sample context into State", use_container_width=True):
            st.session_state["state_text"] = (
                "Skills: Python, SQL, REST APIs, Git, basic ML (pandas, scikit-learn). "
                "Study time: 20 hrs/week. Budget: $0. Runway: 3 months. "
                "Goal: Transition into AI/ML role within 90 days."
            )
            st.session_state["state_mode"] = "Plain text"
            st.rerun()

run_button_text = "🚀 Run Decision" if not st.session_state.compare_mode else "🚀 Run Comparison"

if st.button(
    run_button_text,
    type="primary",
    use_container_width=True,
):
    if not has_valid_state:
        st.error("❌ **Cannot run decision:** The **📝 State** section above is empty. Decision models evaluate input context to make decisions. Please scroll up and enter text or JSON in the State box.")
    elif not has_questions:
        st.error("❌ **Cannot run decision:** Please add at least one question in **❓ Questions**.")
    elif not has_models:
        st.error("❌ **Cannot run decision:** Please select at least one model in the sidebar.")
    else:
        def execute_one(model_name: str) -> dict:
            if is_simulation or not connected:
                return simulate_decision(model_name, state_value, questions)
            elif chosen_engine == "TypeSafe SDK" and is_typesafe_available():
                return run_decision_typesafe(model_name, state_value, questions)
            else:
                return run_decision(model_name, state_value, questions)


    if st.session_state.compare_mode:
        # ── Compare mode ──────────────────────────────────────
        comparison_results = []
        progress = st.progress(0, text="Running decisions…")
        for i, model in enumerate(selected_models):
            progress.progress(
                (i + 1) / len(selected_models),
                text=f"Evaluating {model}…",
            )
            try:
                result = execute_one(model)
                comparison_results.append((model, result))
                st.session_state.history.append({
                    "model": model,
                    "state": state_value,
                    "questions": questions,
                    "result": result,
                })
            except Exception as e:
                st.error(f"❌ Error with {model}: {e}")
        progress.empty()

        if comparison_results:
            st.markdown("---")
            st.markdown("## 📊 Comparison Results")
            render_comparison(comparison_results)
    else:
        # ── Single model mode ──────────────────────────────────
        model = selected_models[0]
        spinner_msg = f"Evaluating decision with `{model}`…" if not is_simulation else f"Simulating decision with `{model}`…"
        with st.spinner(spinner_msg):
            try:
                result = execute_one(model)
                st.session_state.last_result = {
                    "model": model,
                    "state": state_value,
                    "questions": questions,
                    "result": result,
                }
                st.session_state.history.append(st.session_state.last_result)
            except Exception as e:
                st.error(f"❌ Error: {e}")
                st.session_state.last_result = None

# ── Results display ───────────────────────────────────────────────
if (
    st.session_state.last_result
    and not st.session_state.compare_mode
):
    entry = st.session_state.last_result
    st.markdown("---")
    st.markdown(f"## 📊 Results — `{entry['model']}`")
    render_results(entry["result"])
