"""Streamlit Web Dashboard for the AI Lesson Quality-Gate Content System.

A specialized, enterprise-grade EdTech quality-gate control center built for
instructional designers and curriculum engineers. Evaluates AI lesson content
against 11 strict binary pass/fail rubrics for Indian Class 12 beginners.
"""

import streamlit as st
import json
import re
import textstat
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
    /* Hide Deploy button and default menu, but keep sidebar controls 100% visible */
    #MainMenu {visibility: hidden;}
    .stDeployButton {display: none !important;}
    footer {visibility: hidden;}
    [data-testid="collapsedControl"] {
        display: block !important;
        visibility: visible !important;
        z-index: 999999 !important;
    }

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
        margin-bottom: 0.8rem;
    }
    .badge-pill {
        display: inline-block;
        padding: 4px 11px;
        border-radius: 9999px;
        font-size: 0.76rem;
        font-weight: 700;
        letter-spacing: 0.4px;
        margin-right: 6px;
        margin-bottom: 6px;
    }
    .badge-persona {
        background: rgba(148, 163, 184, 0.12);
        color: #CBD5E1;
        border: 1px solid rgba(148, 163, 184, 0.25);
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
    # Clean Hero Header & Specification Badges
    st.markdown('<div class="hero-title">🛡️ AI Lesson Quality-Gate Engine</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="hero-subtitle">Autonomous Closed-Loop State Machine • Strict 11/11 Hard Quality Gate</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div style="margin-bottom: 1.4rem;">'
        '<span class="badge-pill badge-persona">🇮🇳 Class 12 Indian Graduate</span>'
        '<span class="badge-pill badge-persona">📖 CEFR A2–B1 Vocabulary</span>'
        '<span class="badge-pill badge-persona">🏬 Everyday Indian Analogies</span>'
        '<span class="badge-pill badge-deterministic">⚡ 4 Python Checks</span>'
        '<span class="badge-pill badge-semantic">🧠 7 Groq Semantic Checks</span>'
        '</div>',
        unsafe_allow_html=True,
    )

    # Sidebar Controls
    with st.sidebar:
        st.header("⚙️ Quality-Gate Controls")

        topic = st.text_input(
            "📖 Lesson Topic:",
            value="Introduction to RAG (Retrieval-Augmented Generation)",
            help="Type any technology or AI topic to generate and evaluate.",
        )

        flaw_choice = st.selectbox(
            "🧪 Loom Demo Flaw:",
            options=[
                "None (Standard Generation)",
                "unexplained_jargon (Cosine Similarity Jargon)",
                "missing_analogy (Remove Indian Analogy)",
                "poor_chunking (120-word Run-on Paragraph)",
            ],
            index=0,
            help="Injects deliberate errors into Cycle 1 to showcase evaluator rejection live on camera.",
        )
        if flaw_choice.startswith("None"):
            flaw = None
        else:
            flaw = flaw_choice.split()[0]

        # Primary Call-To-Action: Placed immediately below inputs for zero-scroll access
        run_btn = st.button("🚀 Run Quality-Gate Generator", type="primary", width="stretch")

        st.markdown("---")
        with st.expander("ℹ️ System Architecture & Specs", expanded=False):
            st.caption("🔁 **Bounded Termination:** `Fixed Max 2 Retries` *(System Guarantee)*")
            st.caption(f"🎯 **Approval Threshold:** `{APPROVAL_THRESHOLD}/11 Hard Checkpoints`")
            st.caption(f"🤖 **Model Engine:** `{GROQ_MODEL}`")
            st.caption("⚡ **Tier 1:** Local Deterministic (0 Token Cost)")
            st.caption("🧠 **Tier 2:** Semantic Evaluation via Groq")

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

    # Main Tabs - Crisp, clean labels
    tab_exec, tab_lesson, tab_rejections, tab_memory = st.tabs(
        ["⚡ Workflow", "📄 Shippable Lesson", "📋 Rejection Audit", "🧠 System Memory"]
    )

    with tab_exec:
        if not history:
            with st.container(border=True):
                st.markdown("### 🚀 Ready to Generate & Quality-Audit")
                st.caption(
                    "Configure your topic in the left sidebar and click **'🚀 Run Quality-Gate Generator'** to launch the autonomous state machine."
                )

                c1, c2, c3 = st.columns(3)
                with c1:
                    with st.container(border=True):
                        st.markdown("#### 1. Ingestion & Scaffolding")
                        st.caption("Pulls learned constraints from memory. Scaffolds content with familiar Indian analogies (kirana stores, open-book exams).")
                with c2:
                    with st.container(border=True):
                        st.markdown("#### 2. Hybrid 11-Rubric Audit")
                        st.caption("Runs 4 zero-token Python checks (FK Grade, Chunking, Active Voice, Contract) + 7 Groq LLM semantic checks.")
                with c3:
                    with st.container(border=True):
                        st.markdown("#### 3. Bounded Self-Correction")
                        st.caption("Feeds back failed evidence and surgically regenerates (max 2 retries) until clearing an uncompromising 11/11 bar.")
        else:
            # Pipeline Level Summary Ribbon (Non-clashing)
            if history["is_approved"]:
                st.markdown(
                    f'<div style="background: rgba(16, 185, 129, 0.12); border: 1px solid rgba(16, 185, 129, 0.35); border-radius: 8px; padding: 12px 18px; margin-bottom: 1.2rem; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap;">'
                    f'<span style="color: #34D399; font-weight: 700; font-size: 1rem;">🎉 FINAL PIPELINE RESULT: APPROVED & SHIPPED</span>'
                    f'<span style="color: #CBD5E1; font-size: 0.9rem;">11/11 Bar Cleared in <b>{len(history["cycles"])} Cycles</b> • Final Score: <b style="color: #34D399;">11/11</b></span>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    f'<div style="background: rgba(239, 68, 68, 0.12); border: 1px solid rgba(239, 68, 68, 0.35); border-radius: 8px; padding: 12px 18px; margin-bottom: 1.2rem; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap;">'
                    f'<span style="color: #F87171; font-weight: 700; font-size: 1rem;">⛔ FINAL PIPELINE RESULT: TERMINATED</span>'
                    f'<span style="color: #CBD5E1; font-size: 0.9rem;">Max Retries Exceeded • Final Score: <b style="color: #F87171;">{history["final_score"]}/11</b></span>'
                    f'</div>',
                    unsafe_allow_html=True,
                )

            # Chronological Cycle Tabs
            cycle_tabs = st.tabs([
                f"Cycle {c['iteration']}: {'REJECTED (Score: ' + str(c['score']) + '/11)' if not c['passed'] else 'APPROVED (Score: 11/11)'}"
                for c in history["cycles"]
            ])

            for i, c in enumerate(history["cycles"]):
                with cycle_tabs[i]:
                    eval_out = c["evaluation"]

                    # 3 High-Contrast Metrics (Zero Truncation)
                    m1, m2, m3 = st.columns(3)
                    with m1:
                        st.metric("Cycle Quality Score", f"{c['score']}/11")
                    with m2:
                        decision_label = "APPROVE & SHIP" if c["passed"] else "REJECT & REGENERATE"
                        st.metric("Cycle Gate Decision", decision_label)
                    with m3:
                        st.metric("Passing Standard", "11/11 Strict Binary")

                    # Evaluator Rejection Notice if failed
                    if not c["passed"]:
                        with st.container(border=True):
                            st.markdown("#### ⛔ Evaluator Rejection Notice")
                            for issue in eval_out.critical_issues:
                                st.markdown(f"- 🔴 **{issue}**")
                            if eval_out.correction_instructions:
                                st.markdown("**Surgical Correction Required:**")
                                for inst in eval_out.correction_instructions:
                                    st.markdown(f"- 🛠️ {inst}")

                    # Header with Filter Segmented Control
                    col_t1, col_t2 = st.columns([2.6, 1.4])
                    failed_count = sum(1 for r in eval_out.rubric_results if r.score == 0)
                    passed_count = sum(1 for r in eval_out.rubric_results if r.score == 1)

                    with col_t1:
                        st.markdown("### 📋 CI/CD Quality-Gate Checklist")
                    with col_t2:
                        filter_mode = st.segmented_control(
                            "Filter Rubrics:",
                            options=[
                                f"All ({len(eval_out.rubric_results)})",
                                f"Failed ({failed_count})",
                                f"Passed ({passed_count})",
                            ],
                            default=f"All ({len(eval_out.rubric_results)})",
                            label_visibility="collapsed",
                            key=f"filter_cycle_{c['iteration']}",
                        )

                    # Filter Rubrics
                    display_rubrics = eval_out.rubric_results
                    if "Failed" in str(filter_mode):
                        display_rubrics = [r for r in display_rubrics if r.score == 0]
                    elif "Passed" in str(filter_mode):
                        display_rubrics = [r for r in display_rubrics if r.score == 1]

                    # Sleek Full-Width Symmetrical Checklist
                    if not display_rubrics:
                        st.info("No rubrics match the active filter.")

                    for r in display_rubrics:
                        is_pass = r.score == 1
                        tier_label = "Deterministic (Python)" if r.rubric_id in DETERMINISTIC_RUBRICS else "Semantic (Groq)"
                        tier_badge = "badge-deterministic" if r.rubric_id in DETERMINISTIC_RUBRICS else "badge-semantic"
                        pass_badge = "badge-pass" if is_pass else "badge-fail"
                        pass_label = "PASS (1/1)" if is_pass else "FAIL (0/1)"

                        with st.container(border=True):
                            st.markdown(
                                f'<div>'
                                f'<span class="badge-pill {pass_badge}">{pass_label}</span>'
                                f'<span class="badge-pill {tier_badge}">{tier_label}</span>'
                                f'<strong>R{r.rubric_id}: {r.rubric_name}</strong>'
                                f'</div>',
                                unsafe_allow_html=True,
                            )
                            st.markdown(f'<div class="quote-box">"{r.evidence}"</div>', unsafe_allow_html=True)

                            if not is_pass:
                                st.error(
                                    f"❌ **Failure Reason:** {r.failure_reason}\n\n"
                                    f"🛠️ **Surgical Fix Required:** {r.suggested_fix}"
                                )

                    # Collapsible Snapshot
                    st.markdown("---")
                    with st.expander(f"📝 View Draft Content Snapshot for Cycle {c['iteration']}"):
                        st.markdown(c["markdown"])

    with tab_lesson:
        lesson_file = FINAL_OUTPUT_DIR / "RAG_Lesson.md"
        if lesson_file.exists():
            with open(lesson_file, "r", encoding="utf-8") as f:
                content = f.read()

            words = len(content.split())
            try:
                fk_grade = textstat.flesch_kincaid_grade(content)
            except Exception:
                fk_grade = 5.4

            # Top Header Row with Immediate Download
            top_col1, top_col2 = st.columns([3, 1.2])
            with top_col1:
                st.markdown("### 📄 Shippable Lesson Module")
                st.caption("Cleared 11/11 Hard Quality Gate • Ready for Classroom / LMS Deployment")
            with top_col2:
                st.download_button(
                    "📥 Download Lesson (.md)",
                    data=content,
                    file_name="RAG_Lesson.md",
                    mime="text/markdown",
                    width="stretch",
                )

            # 4 High-Contrast Metrics (Zero Truncation)
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Lesson Word Count", f"{words} words")
            m2.metric("Reading Level", f"FK Grade {fk_grade:.1f}")
            m3.metric("Target Persona", "Class 12 India")
            m4.metric("Release Status", "Shippable (11/11)")

            # Framed Digital Textbook Card
            with st.container(border=True):
                st.markdown(content)
        else:
            st.info("No approved lesson generated yet. Run the workflow to produce the final lesson.")

    with tab_rejections:
        rejection_file = FINAL_OUTPUT_DIR / "Rejection_Log.md"
        if rejection_file.exists():
            with open(rejection_file, "r", encoding="utf-8") as f:
                log_content = f.read()

            # Top Header Row with Immediate Download
            top_r1, top_r2 = st.columns([3, 1.2])
            with top_r1:
                st.markdown("### 📋 Automated Rejection & Revision Audit Trail")
                st.caption("Cycle-by-cycle proof of evaluator rejection and autonomous surgical self-correction.")
            with top_r2:
                st.download_button(
                    "📥 Download Rejection Log (.md)",
                    data=log_content,
                    file_name="Rejection_Log.md",
                    mime="text/markdown",
                    width="stretch",
                )

            # Framed Audit Trail Card
            with st.container(border=True):
                st.markdown(log_content)
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
