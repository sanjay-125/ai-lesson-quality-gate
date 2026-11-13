"""Streamlit Web Dashboard for the AI Lesson Quality-Gate Content System.

A specialized, enterprise-grade EdTech quality-gate control center built for
instructional designers and curriculum engineers. Evaluates AI lesson content
against 11 strict binary pass/fail rubrics for Indian Class 12 beginners.
"""

import streamlit as st
import json
import re
from pathlib import Path
from datetime import datetime
from src.config import GROQ_MODEL, APPROVAL_THRESHOLD, MAX_RETRIES, FINAL_OUTPUT_DIR
from src.graph import QualityGateWorkflow
from src.memory import memory_store

# Page configuration
st.set_page_config(
    page_title="AI Lesson Quality-Gate Engine",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom High-Contrast Theme-Adaptive CSS
st.markdown(
    """
    <style>
    /* Theme-Adaptive Gradient Title */
    .hero-title {
        background: linear-gradient(135deg, #38BDF8 0%, #818CF8 50%, #C084FC 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 2.35rem;
        font-weight: 850;
        letter-spacing: -0.6px;
        margin-bottom: 0.2rem;
    }
    .hero-subtitle {
        color: #94A3B8;
        font-size: 1.05rem;
        font-weight: 450;
        margin-bottom: 1.2rem;
    }
    .badge-pill {
        display: inline-block;
        padding: 3px 10px;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 0.4px;
        text-transform: uppercase;
        margin-right: 6px;
    }
    .badge-deterministic {
        background: rgba(56, 189, 248, 0.15);
        color: #38BDF8;
        border: 1px solid rgba(56, 189, 248, 0.35);
    }
    .badge-semantic {
        background: rgba(168, 85, 247, 0.15);
        color: #C084FC;
        border: 1px solid rgba(168, 85, 247, 0.35);
    }
    .badge-pass {
        background: rgba(16, 185, 129, 0.15);
        color: #34D399;
        border: 1px solid rgba(16, 185, 129, 0.35);
    }
    .badge-fail {
        background: rgba(239, 68, 68, 0.15);
        color: #F87171;
        border: 1px solid rgba(239, 68, 68, 0.35);
    }
    .quote-box {
        background: rgba(128, 128, 128, 0.08);
        border-left: 3px solid #818CF8;
        padding: 8px 12px;
        border-radius: 4px;
        font-size: 0.88rem;
        font-style: italic;
        margin: 6px 0;
    }
    .evidence-label {
        font-size: 0.78rem;
        font-weight: 700;
        color: #94A3B8;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Rubric Metadata
DETERMINISTIC_RUBRICS = {1, 7, 9, 11}


def get_rubric_tier(r_id: int) -> str:
    return "⚡ Deterministic (Python)" if r_id in DETERMINISTIC_RUBRICS else "🧠 Semantic (Groq)"


def main():
    # Hero Banner
    col_h1, col_h2 = st.columns([3.5, 1.2])
    with col_h1:
        st.markdown('<div class="hero-title">🛡️ AI Lesson Quality-Gate Engine</div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="hero-subtitle">Autonomous Closed-Loop State Machine • Strict 11/11 Binary Gating • Indian Beginner Pedagogy</div>',
            unsafe_allow_html=True,
        )
    with col_h2:
        with st.container(border=True):
            st.caption("🎯 **Target Persona:** Class 12 Pass-out")
            st.caption("📚 **Vocabulary:** CEFR A2–B1 (No CS/Math)")
            st.caption("🏬 **Analogy Anchor:** Everyday Indian Life")

    # Sidebar Controls
    with st.sidebar:
        st.header("⚙️ Quality-Gate Controls")

        topic = st.text_input(
            "📖 Lesson Topic:",
            value="Introduction to RAG (Retrieval-Augmented Generation)",
            help="Type any technology or AI topic to generate and evaluate.",
        )

        st.markdown("---")
        st.subheader("🧪 Loom Demo Flaw Injection")
        st.caption("Injects deliberate errors into Cycle 1 to showcase evaluator rejection live on camera:")
        flaw_choice = st.selectbox(
            "Deliberate Flaw:",
            options=[
                "None (Standard Generation)",
                "unexplained_jargon (Cosine Similarity Jargon)",
                "missing_analogy (Remove Indian Analogy)",
                "poor_chunking (120-word Run-on Paragraph)",
            ],
            index=0,
        )
        if flaw_choice.startswith("None"):
            flaw = None
        else:
            flaw = flaw_choice.split()[0]

        st.markdown("---")
        st.caption("🔁 **Bounded Termination:** `Fixed Max 2 Retries` *(System Guarantee)*")
        st.caption(f"🎯 **Approval Threshold:** `{APPROVAL_THRESHOLD}/11 Hard Checkpoints`")
        st.caption(f"🤖 **Model Engine:** `{GROQ_MODEL}`")
        st.caption("⚡ **Tier 1:** Local Deterministic (0 Token Cost)")
        st.caption("🧠 **Tier 2:** Semantic Evaluation via Groq")

        run_btn = st.button("🚀 Run Quality-Gate Generator", type="primary", width="stretch")

    # Workflow Session State
    if "workflow_history" not in st.session_state:
        st.session_state.workflow_history = None

    # Workflow Execution
    if run_btn:
        with st.spinner("Executing agentic evaluation loop..."):
            workflow = QualityGateWorkflow(topic=topic, max_retries=MAX_RETRIES)
            cycles_data = []

            prog_bar = st.progress(0, text="Step 1/4: Retrieving learned negative constraints from persistent memory...")
            status_box = st.empty()

            for update in workflow.run_step_by_step(deliberate_flaw=flaw):
                step = update["step"]
                if step == "MEMORY_RETRIEVED":
                    prog_bar.progress(20, text="Step 1/4: Memory loaded.")
                    status_box.info(f"Loaded {len(update['rules'])} evolving negative constraints from past runs.")

                elif step == "GENERATED":
                    prog_bar.progress(40, text=f"Step 2/4: Cycle {update['iteration']} draft produced.")
                    status_box.info(f"Cycle {update['iteration']}: Lesson drafted ({len(update['markdown'].split())} words).")

                elif step == "EVALUATED":
                    prog_bar.progress(70, text=f"Step 3/4: Cycle {update['iteration']} quality evaluation completed.")
                    eval_out = update["evaluation"]
                    cycles_data.append({
                        "iteration": update["iteration"],
                        "score": update["score"],
                        "passed": update["passed"],
                        "evaluation": eval_out,
                        "markdown": workflow.current_markdown,
                    })

                elif step == "REGENERATING":
                    prog_bar.progress(85, text="Step 4/4: Feeding back critique for surgical self-correction...")
                    status_box.warning("Feedback fed back to generator. Applying surgical fixes to quoted evidence...")

                elif step == "COMPLETE":
                    prog_bar.progress(100, text="Workflow complete!")
                    st.session_state.workflow_history = {
                        "topic": topic,
                        "is_approved": update["is_approved"],
                        "final_score": update["final_score"],
                        "cycles": cycles_data,
                        "rejection_log": update["rejection_log"],
                        "final_markdown": update["lesson_markdown"],
                    }

    history = st.session_state.workflow_history

    # Main Tabs
    tab_exec, tab_lesson, tab_rejections, tab_memory = st.tabs(
        ["📊 Live Workflow Execution", "📄 Shippable Lesson", "📋 Rejection Audit Log", "🧠 Evolving Memory"]
    )

    with tab_exec:
        if not history:
            st.info("👈 Select a topic in the sidebar and click **'🚀 Run Quality-Gate Generator'** to begin.")
        else:
            # Banner
            if history["is_approved"]:
                st.success(
                    f"🎉 **APPROVED & CLEARED FOR SHIPPING!** Final Score: **{history['final_score']}/11** • Total Cycles: **{len(history['cycles'])}**"
                )
            else:
                st.error(
                    f"⛔ **TERMINATED WITHOUT CLEARING QUALITY BAR:** Final Score: **{history['final_score']}/11** • Max Retries Exceeded"
                )

            # Cycle Tabs
            cycle_tabs = st.tabs([f"Cycle {c['iteration']} ({c['score']}/11 - {'PASS' if c['passed'] else 'FAIL'})" for c in history["cycles"]])

            for i, c in enumerate(history["cycles"]):
                with cycle_tabs[i]:
                    eval_out = c["evaluation"]

                    # Top Metrics
                    m1, m2, m3, m4 = st.columns(4)
                    with m1:
                        st.metric("Total Score", f"{c['score']}/11")
                    with m2:
                        st.metric("Quality Status", eval_out.overall_status)
                    with m3:
                        st.metric("Decision", eval_out.final_recommendation)
                    with m4:
                        st.metric("Approval Bar", "11/11 (Strict Binary)")

                    # Critical Issues Banner if failed
                    if not c["passed"]:
                        with st.container(border=True):
                            st.markdown("#### ⛔ Evaluator Rejection Notice")
                            for issue in eval_out.critical_issues:
                                st.markdown(f"- 🔴 **{issue}**")
                            if eval_out.correction_instructions:
                                st.markdown("**Surgical Correction Required:**")
                                for inst in eval_out.correction_instructions:
                                    st.markdown(f"- 🛠️ {inst}")

                    st.markdown("### 📋 11-Rubric Quality Matrix")

                    # 2-Column Rubric Matrix Cards
                    col_left, col_right = st.columns(2)
                    for idx, r in enumerate(eval_out.rubric_results):
                        target_col = col_left if idx % 2 == 0 else col_right
                        with target_col:
                            with st.container(border=True):
                                # Rubric Header with Badges
                                is_pass = r.score == 1
                                tier_badge = "badge-deterministic" if r.rubric_id in DETERMINISTIC_RUBRICS else "badge-semantic"
                                tier_label = "Deterministic" if r.rubric_id in DETERMINISTIC_RUBRICS else "Semantic"
                                pass_badge = "badge-pass" if is_pass else "badge-fail"
                                pass_label = "PASS (1/1)" if is_pass else "FAIL (0/1)"

                                st.markdown(
                                    f'<div>'
                                    f'<span class="badge-pill {pass_badge}">{pass_label}</span>'
                                    f'<span class="badge-pill {tier_badge}">{tier_label}</span>'
                                    f'<strong>R{r.rubric_id}: {r.rubric_name}</strong>'
                                    f'</div>',
                                    unsafe_allow_html=True,
                                )

                                # Quoted Evidence
                                st.markdown('<div class="evidence-label">Quoted Evidence / Rationale:</div>', unsafe_allow_html=True)
                                st.markdown(f'<div class="quote-box">"{r.evidence}"</div>', unsafe_allow_html=True)

                                # Failure Details
                                if not is_pass:
                                    if r.failure_reason:
                                        st.error(f"**Failure Reason:** {r.failure_reason}")
                                    if r.suggested_fix:
                                        st.info(f"**Action Required:** {r.suggested_fix}")

                    # Collapsible Snapshot
                    st.markdown("---")
                    with st.expander(f"📝 View Draft Content Snapshot for Cycle {c['iteration']}"):
                        st.markdown(c["markdown"])

    with tab_lesson:
        st.subheader("📄 Final Shippable Lesson Output")
        lesson_file = FINAL_OUTPUT_DIR / "RAG_Lesson.md"
        if lesson_file.exists():
            with open(lesson_file, "r", encoding="utf-8") as f:
                content = f.read()

            words = len(content.split())
            paras = len([p for p in content.split("\n\n") if p.strip() and not p.startswith("#")])

            c1, c2, c3 = st.columns(3)
            c1.metric("Lesson Word Count", f"{words} words")
            c2.metric("Substantive Paragraphs", f"{paras} paragraphs")
            c3.metric("Shippable Target", "Class 12 Indian Graduate")

            st.markdown(content)
            st.download_button(
                "📥 Download Shippable Lesson (.md)",
                data=content,
                file_name="RAG_Lesson.md",
                mime="text/markdown",
                width="stretch",
            )
        else:
            st.info("No approved lesson generated yet. Run the workflow to produce the final lesson.")

    with tab_rejections:
        st.subheader("📋 Quality-Gate Rejection & Revision Audit Trail")
        rejection_file = FINAL_OUTPUT_DIR / "Rejection_Log.md"
        if rejection_file.exists():
            with open(rejection_file, "r", encoding="utf-8") as f:
                log_content = f.read()
            st.markdown(log_content)
            st.download_button(
                "📥 Download Rejection Audit Log (.md)",
                data=log_content,
                file_name="Rejection_Log.md",
                mime="text/markdown",
                width="stretch",
            )
        else:
            st.info("No rejection log generated yet.")

    with tab_memory:
        st.subheader("🧠 Persistent Cross-Run Memory & Self-Evolution")
        st.caption("The engine tracks error frequencies across runs and synthesizes dynamic negative constraints.")

        mem_data = memory_store.load()

        m1, m2, m3, m4 = st.columns(4)
        total_r = mem_data.get("total_runs", 0)
        succ_r = mem_data.get("successful_runs", 0)
        fail_r = mem_data.get("failed_runs", 0)
        pass_rate = f"{(succ_r / total_r * 100):.1f}%" if total_r > 0 else "N/A"

        m1.metric("Total System Runs", total_r)
        m2.metric("Approved & Shipped", succ_r)
        m3.metric("Terminated / Rejected", fail_r)
        m4.metric("Approval Rate", pass_rate)

        st.markdown("### 🛡️ Dynamic Negative Constraints (Learned from Past Failures)")
        for rule in mem_data.get("learned_negative_constraints", []):
            with st.container(border=True):
                st.markdown(f"⚠️ **Constraint:** {rule}")

        st.markdown("### 📈 Historical Runs Audit")
        history_list = mem_data.get("history", [])
        if history_list:
            display_history = []
            for h in reversed(history_list[-10:]):
                display_history.append({
                    "Run ID": h.get("run_id"),
                    "Topic": h.get("topic"),
                    "Score": f"{h.get('final_score')}/11",
                    "Passed": "✅ Yes" if h.get("passed") else "❌ No",
                    "Iterations": h.get("iterations"),
                    "Timestamp": h.get("timestamp", "")[:19].replace("T", " "),
                })
            st.dataframe(display_history, width="stretch")
        else:
            st.info("No run history recorded yet.")


if __name__ == "__main__":
    main()
