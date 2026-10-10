"""
Result visualization — render /v1/systemone answers
as interactive Plotly charts, gauges, and metrics.
"""

import json
import streamlit as st
import plotly.graph_objects as go


# ── Color palette ──────────────────────────────────────────────────────────

COLORS = {
    "primary": "#6C63FF",
    "secondary": "#3B82F6",
    "accent": "#8B5CF6",
    "success": "#10B981",
    "warning": "#F59E0B",
    "danger": "#EF4444",
    "surface": "#1E1E2E",
    "surface_light": "#2A2A3E",
    "text": "#E2E8F0",
    "text_muted": "#94A3B8",
}

CHART_COLORS = [
    "#6C63FF", "#3B82F6", "#8B5CF6", "#10B981",
    "#F59E0B", "#EF4444", "#06B6D4", "#EC4899",
    "#84CC16", "#F97316", "#14B8A6", "#A855F7",
]


def render_results(result: dict):
    """Render the full decision result with charts and metrics."""
    answers = result.get("answers", {})
    usage = result.get("usage", {})
    latency = result.get("_latency_ms", 0)
    is_simulated = result.get("_simulated", False)

    if is_simulated:
        st.info("💡 **Showing Simulated Output:** This result was generated via the built-in decision simulation engine. Switch to a live model once pulled.")

    # ── Top metrics row ────────────────────────────────────────────
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.metric("⚡ Latency", f"{latency:.0f} ms")
    with m2:
        st.metric("📥 Input Tokens", usage.get("input_tokens", "—"))
    with m3:
        st.metric("📤 Output Tokens", usage.get("output_tokens", "—"))
    with m4:
        st.metric("❓ Questions Evaluated", len(answers))

    st.divider()

    # ── Render each answer ─────────────────────────────────────────
    for q_name, answer in answers.items():
        q_type = answer.get("type", "unknown")
        st.subheader(f"📌 {q_name}")

        if q_type == "choice":
            _render_choice_result(q_name, answer)
        elif q_type == "noul":
            _render_noul_result(q_name, answer)
        elif q_type == "score":
            _render_score_result(q_name, answer)
        else:
            st.json(answer)

        st.divider()

    # ── Raw JSON & Export ──────────────────────────────────────────
    with st.expander("🔍 Raw API Response & Export"):
        json_str = json.dumps(result, indent=2, default=str)
        st.download_button(
            "💾 Download Result JSON",
            data=json_str,
            file_name="decision_result.json",
            mime="application/json",
            use_container_width=True,
        )
        st.code(json_str, language="json")


def _render_choice_result(name: str, answer: dict):
    """Render a choice answer as a horizontal bar chart."""
    choice = answer.get("choice", "?")
    probs = answer.get("probabilities", {})
    confidence = answer.get("confidence", 0)

    # Decision card
    st.success(f"**Decision:** `{choice}`  ·  Confidence: `{confidence:.2f}`")

    if probs:
        # Sort by probability descending
        sorted_items = sorted(probs.items(), key=lambda x: x[1], reverse=True)
        labels = [item[0] for item in sorted_items]
        values = [item[1] for item in sorted_items]
        colors = []
        for label in labels:
            if label == choice:
                colors.append(COLORS["success"])
            else:
                colors.append(COLORS["surface_light"])

        fig = go.Figure(go.Bar(
            x=values,
            y=labels,
            orientation="h",
            marker_color=colors,
            text=[f"{v:.1%}" for v in values],
            textposition="auto",
            textfont=dict(color="white", size=13),
        ))
        fig.update_layout(
            height=max(180, len(labels) * 48),
            margin=dict(l=0, r=20, t=10, b=10),
            xaxis=dict(
                range=[0, 1],
                tickformat=".0%",
                showgrid=True,
                gridcolor="rgba(255,255,255,0.05)",
            ),
            yaxis=dict(autorange="reversed"),
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color=COLORS["text"], size=13),
        )
        st.plotly_chart(fig, use_container_width=True, key=f"chart_choice_{name}")


def _render_noul_result(name: str, answer: dict):
    """Render a noul (boolean) answer as a probability gauge."""
    noul_value = answer.get("noul", 0)

    # Color based on value
    if noul_value >= 0.7:
        color = COLORS["success"]
        label = "Likely TRUE"
    elif noul_value <= 0.3:
        color = COLORS["danger"]
        label = "Likely FALSE"
    else:
        color = COLORS["warning"]
        label = "Uncertain"

    col1, col2 = st.columns([1, 2])
    with col1:
        st.metric("Probability (True)", f"{noul_value:.1%}")
        st.caption(label)

    with col2:
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=noul_value * 100,
            number={"suffix": "%", "font": {"size": 28, "color": "white"}},
            gauge={
                "axis": {
                    "range": [0, 100],
                    "tickfont": {"color": "rgba(255,255,255,0.5)", "size": 10},
                },
                "bar": {"color": color, "thickness": 0.6},
                "bgcolor": "rgba(255,255,255,0.05)",
                "borderwidth": 0,
                "steps": [
                    {"range": [0, 30], "color": "rgba(239,68,68,0.15)"},
                    {"range": [30, 70], "color": "rgba(245,158,11,0.15)"},
                    {"range": [70, 100], "color": "rgba(16,185,129,0.15)"},
                ],
                "threshold": {
                    "line": {"color": "white", "width": 2},
                    "thickness": 0.8,
                    "value": noul_value * 100,
                },
            },
        ))
        fig.update_layout(
            height=200,
            margin=dict(l=30, r=30, t=40, b=10),
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color="white"),
        )
        st.plotly_chart(fig, use_container_width=True, key=f"chart_noul_{name}")


def _render_score_result(name: str, answer: dict):
    """Render a score answer as a bar chart across rubric levels."""
    score_val = answer.get("score", 0)
    legend = answer.get("legend", {})
    probs = answer.get("probabilities", {})
    confidence = answer.get("confidence", 0)

    try:
        max_level = max(int(k) for k in probs.keys()) if probs else 0
    except (ValueError, TypeError):
        max_level = len(probs) - 1 if probs else 0

    st.info(f"**Expected Score:** `{score_val:.2f}` / `{max_level}.0`  ·  Confidence: `{confidence:.2f}`")

    if probs:
        try:
            levels = sorted(probs.keys(), key=lambda x: int(x))
        except (ValueError, TypeError):
            levels = list(probs.keys())

        labels = [f"Level {l}: {legend.get(l, legend.get(int(l) if str(l).isdigit() else l, ''))}" for l in levels]
        values = [probs[l] for l in levels]

        # Color gradient from red → yellow → green
        n = len(levels)
        colors = []
        for i in range(n):
            ratio = i / max(n - 1, 1)
            if ratio < 0.5:
                colors.append(COLORS["danger"])
            elif ratio < 0.75:
                colors.append(COLORS["warning"])
            else:
                colors.append(COLORS["success"])

        fig = go.Figure(go.Bar(
            x=values,
            y=labels,
            orientation="h",
            marker_color=colors,
            text=[f"{v:.1%}" for v in values],
            textposition="auto",
            textfont=dict(color="white", size=13),
        ))
        fig.update_layout(
            height=max(180, len(labels) * 55),
            margin=dict(l=0, r=20, t=10, b=10),
            xaxis=dict(
                range=[0, 1],
                tickformat=".0%",
                showgrid=True,
                gridcolor="rgba(255,255,255,0.05)",
            ),
            yaxis=dict(autorange="reversed"),
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color=COLORS["text"], size=12),
        )
        st.plotly_chart(fig, use_container_width=True, key=f"chart_score_{name}")


def render_comparison(results: list[tuple[str, dict]]):
    """
    Render side-by-side results from multiple models.
    results: list of (model_name, result_dict)
    """
    if len(results) < 2:
        st.warning("Select at least 2 models for comparison.")
        return

    # ── Latency comparison ─────────────────────────────────────────
    st.subheader("⚡ Latency Comparison")
    model_names = [r[0] for r in results]
    latencies = [r[1].get("_latency_ms", 0) for r in results]

    fig = go.Figure(go.Bar(
        x=model_names,
        y=latencies,
        marker_color=CHART_COLORS[:len(model_names)],
        text=[f"{l:.0f} ms" for l in latencies],
        textposition="auto",
        textfont=dict(color="white", size=14),
    ))
    fig.update_layout(
        height=250,
        margin=dict(l=0, r=0, t=10, b=10),
        yaxis_title="Latency (ms)",
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color=COLORS["text"]),
    )
    st.plotly_chart(fig, use_container_width=True, key="comparison_latency")

    st.divider()

    # ── Per-question comparison ────────────────────────────────────
    first_answers = results[0][1].get("answers", {})
    for q_name in first_answers.keys():
        st.subheader(f"📌 {q_name}")
        cols = st.columns(len(results))
        for i, (model_name, result) in enumerate(results):
            with cols[i]:
                st.caption(f"**{model_name}**")
                answer = result.get("answers", {}).get(q_name)
                if answer:
                    q_type = answer.get("type")
                    if q_type == "choice":
                        st.success(f"**{answer.get('choice', '?')}** ({answer.get('confidence', 0):.2f})")
                    elif q_type == "noul":
                        val = answer.get("noul", 0)
                        st.metric("P(true)", f"{val:.1%}")
                    elif q_type == "score":
                        st.metric("Score", f"{answer.get('score', 0):.2f}")
                else:
                    st.warning("No answer")
        st.divider()
