"""
Dynamic question builder — renders Streamlit form widgets
for constructing /v1/systemone question schemas.
"""

import json
import streamlit as st


def render_question_builder() -> dict:
    """
    Render the interactive question builder UI.
    Returns a dict of questions ready for the systemone API.
    """
    # Initialize session state
    if "questions" not in st.session_state:
        st.session_state.questions = []

    questions_out: dict = {}

    for idx, q in enumerate(st.session_state.questions):
        q_key = f"q_{idx}"
        with st.container():
            cols = st.columns([3, 2, 1])
            with cols[0]:
                q["name"] = st.text_input(
                    "Question name",
                    value=q.get("name", f"question_{idx + 1}"),
                    key=f"{q_key}_name",
                    help="Unique identifier for this question (used as the key in the response)",
                )
            with cols[1]:
                q["type"] = st.selectbox(
                    "Type",
                    ["choice", "noul", "score"],
                    index=["choice", "noul", "score"].index(q.get("type", "choice")),
                    key=f"{q_key}_type",
                    help="choice = pick from list, noul = true/false, score = rubric level",
                )
            with cols[2]:
                st.write("")  # spacer
                st.write("")
                if st.button("🗑️", key=f"{q_key}_delete", help="Remove this question"):
                    st.session_state.questions.pop(idx)
                    st.rerun()

            q["instructions"] = st.text_area(
                "Instructions",
                value=q.get("instructions", ""),
                key=f"{q_key}_instructions",
                height=68,
                help="What should the model decide? Be specific.",
            )

            # Type-specific criteria
            if q["type"] == "choice":
                _render_choice_criteria(q, q_key)
            elif q["type"] == "noul":
                _render_noul_criteria(q, q_key)
            elif q["type"] == "score":
                _render_score_criteria(q, q_key)

            st.divider()

            # Build question dict
            if q["name"].strip():
                question_obj = {
                    "type": q["type"],
                    "instructions": q["instructions"],
                }
                criteria = q.get("criteria")
                if criteria:
                    question_obj["criteria"] = criteria
                questions_out[q["name"].strip()] = question_obj

    # Add question button
    if st.button("➕ Add Question", use_container_width=True):
        st.session_state.questions.append({
            "name": f"question_{len(st.session_state.questions) + 1}",
            "type": "choice",
            "instructions": "",
            "criteria": {},
        })
        st.rerun()

    return questions_out


def _render_choice_criteria(q: dict, q_key: str):
    """Render editable key-value pairs for choice options."""
    st.caption("Options (2–26)")
    if "criteria" not in q or not isinstance(q["criteria"], dict):
        q["criteria"] = {"option_1": "Description of option 1", "option_2": "Description of option 2"}

    criteria_keys = list(q["criteria"].keys())
    new_criteria = {}

    for i, key in enumerate(criteria_keys):
        c1, c2, c3 = st.columns([2, 3, 0.5])
        with c1:
            new_key = st.text_input(
                "Option",
                value=key,
                key=f"{q_key}_crit_key_{i}",
                label_visibility="collapsed",
                placeholder="Option name",
            )
        with c2:
            new_val = st.text_input(
                "Description",
                value=q["criteria"][key] or "",
                key=f"{q_key}_crit_val_{i}",
                label_visibility="collapsed",
                placeholder="Description (optional, use empty for self-describing)",
            )
        with c3:
            if st.button("✕", key=f"{q_key}_crit_del_{i}"):
                st.session_state.questions[int(q_key.split("_")[1])]["criteria"].pop(key, None)
                st.rerun()
        if new_key.strip():
            new_criteria[new_key.strip()] = new_val.strip() if new_val.strip() else None

    q["criteria"] = new_criteria

    if st.button("＋ Add Option", key=f"{q_key}_add_option"):
        q["criteria"][f"option_{len(q['criteria']) + 1}"] = ""
        st.rerun()


def _render_noul_criteria(q: dict, q_key: str):
    """Render optional true/false descriptions for noul questions."""
    show_criteria = st.checkbox(
        "Add custom true/false descriptions",
        value=bool(q.get("criteria")),
        key=f"{q_key}_noul_custom",
    )
    if show_criteria:
        c1, c2 = st.columns(2)
        if not isinstance(q.get("criteria"), dict):
            q["criteria"] = {"true": "", "false": ""}
        with c1:
            true_desc = st.text_input(
                "True means…",
                value=q["criteria"].get("true", ""),
                key=f"{q_key}_noul_true",
            )
        with c2:
            false_desc = st.text_input(
                "False means…",
                value=q["criteria"].get("false", ""),
                key=f"{q_key}_noul_false",
            )
        q["criteria"] = {"true": true_desc, "false": false_desc}
    else:
        q["criteria"] = None


def _render_score_criteria(q: dict, q_key: str):
    """Render ordered level descriptions for score questions."""
    st.caption("Rubric levels (lowest → highest)")
    if not isinstance(q.get("criteria"), list) or len(q.get("criteria", [])) < 2:
        q["criteria"] = ["Low", "Medium", "High"]

    new_levels = []
    for i, level in enumerate(q["criteria"]):
        c1, c2, c3 = st.columns([0.5, 4, 0.5])
        with c1:
            st.markdown(f"**{i}**")
        with c2:
            new_val = st.text_input(
                f"Level {i}",
                value=level,
                key=f"{q_key}_score_{i}",
                label_visibility="collapsed",
            )
            new_levels.append(new_val)
        with c3:
            if len(q["criteria"]) > 2 and st.button("✕", key=f"{q_key}_score_del_{i}"):
                q["criteria"].pop(i)
                st.rerun()

    q["criteria"] = new_levels

    if st.button("＋ Add Level", key=f"{q_key}_add_level"):
        q["criteria"].append(f"Level {len(q['criteria'])}")
        st.rerun()


def load_questions_from_preset(questions: dict):
    """Load a preset's questions into session state."""
    st.session_state.questions = []
    for name, q_def in questions.items():
        q = {
            "name": name,
            "type": q_def["type"],
            "instructions": q_def.get("instructions", ""),
            "criteria": q_def.get("criteria"),
        }
        st.session_state.questions.append(q)


def get_state_input() -> any:
    """
    Render the state input widget.
    Supports plain text or JSON mode.
    """
    mode = st.radio(
        "State input format",
        ["Plain text", "JSON"],
        horizontal=True,
        help="Plain text for simple inputs, JSON for structured data (objects/arrays)",
    )

    if mode == "Plain text":
        state_val = st.text_area(
            "State (the text to judge)",
            height=120,
            placeholder="Enter the text you want the model to make decisions about…",
            key="state_text",
        )
        return state_val
    else:
        state_json = st.text_area(
            "State (JSON)",
            height=160,
            placeholder='{"from": "user@example.com", "subject": "...", "body": "..."}',
            key="state_json",
        )
        if state_json.strip():
            try:
                return json.loads(state_json)
            except json.JSONDecodeError as e:
                st.error(f"Invalid JSON: {e}")
                return None
        return None
