"""Streamlit Web Dashboard for the AI Lesson Quality-Gate Content System.

Designed for interactive human-in-the-loop demonstrations, real-time rubric auditing,
deliberate error injection showcase, and video recordings.
"""

import streamlit as st
import json
from pathlib import Path
from src.config import GROQ_MODEL, APPROVAL_THRESHOLD, MAX_RETRIES, FINAL_OUTPUT_DIR
from src.graph import QualityGateWorkflow
from src.memory import memory_store

# Page configuration
st.set_page_config(
    page_title="AI Lesson Quality-Gate Engine",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for polished edtech dashboard look
st.markdown(
    """
    <style>
    .main-title {
        font-size: 2.2rem;
        font-weight: 800;
        color: #1E293B;
        margin-bottom: 0.2rem;
    }
    .sub-title {
        font-size: 1.05rem;
        color: #64748B;
        margin-bottom: 1.5rem;
    }
    .metric-card {
        background-color: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        padding: 1rem;
        text-align: center;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        padding: 10px 20px;
        font-weight: 600;
    }
    .rubric-pass {
        color: #15803D;
        background-color: #DCFCE7;
        padding: 4px 10px;
        border-radius: 6px;
        font-weight: 700;
        font-size: 0.85rem;
    }
    .rubric-fail {
        color: #B91C1C;
        background-color: #FEE2E2;
        padding: 4px 10px;
        border-radius: 6px;
        font-weight: 700;
        font-size: 0.85rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def main():
    # Header
    st.markdown('<div class="main-title">🛡️ AI Lesson Quality-Gate Engine</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sub-title">Autonomous Generate ➔ Evaluate ➔ Regenerate loop with strict 11-rubric gating for Indian beginner learners.</div>',
        unsafe_allow_html=True,
    )

    # Sidebar Controls
    with st.sidebar:
        st.header("⚙️ Generation Controls")
        topic = st.text_input("Lesson Topic", value="Introduction to RAG (Retrieval-Augmented Generation)")

        st.info(
            "**Target Learner Persona:**\n"
            "- Class 12 Graduate from India\n"
            "- Non-English Medium background\n"
            "- Limited vocabulary (CEFR A2-B1)\n"
            "- Zero tech/AI prior knowledge\n"
            "- Everyday Indian analogies (Kirana, Exam, Tiffin)"
        )

        st.markdown("---")
        st.subheader("🧪 Loom Demo Flaw Injection")
        flaw_choice = st.selectbox(
            "Inject Deliberate Flaw:",
            options=["None (Standard Generation)", "unexplained_jargon", "missing_analogy", "poor_chunking"],
            help="Deliberately triggers an evaluator rejection to demonstrate strict quality gating on video.",
        )
        flaw = None if flaw_choice.startswith("None") else flaw_choice

        retries = st.slider("Max Allowed Retries", min_value=1, max_value=3, value=MAX_RETRIES)

        st.markdown("---")
        st.caption(f"🤖 **Model:** `{GROQ_MODEL}`")
        st.caption(f"🎯 **Approval Threshold:** `{APPROVAL_THRESHOLD}/11 Hard Checkpoints`")

        run_btn = st.button("🚀 Run Quality-Gate Generator", type="primary", use_container_width=True)

    # Initialize session state for workflow runs
    if "workflow_history" not in st.session_state:
        st.session_state.workflow_history = None

    # Trigger workflow
    if run_btn:
        with st.spinner("Executing agentic evaluation loop..."):
            workflow = QualityGateWorkflow(topic=topic, max_retries=retries)
            cycles_data = []

            progress_bar = st.progress(0, text="Initializing workflow and retrieving memory...")
            status_box = st.empty()

            for update in workflow.run_step_by_step(deliberate_flaw=flaw):
                step = update["step"]
                if step == "MEMORY_RETRIEVED":
                    progress_bar.progress(15, text="Persistent memory loaded.")
                    status_box.info(f"Loaded {len(update['rules'])} evolving negative constraints.")

                elif step == "GENERATED":
                    progress_bar.progress(35, text=f"Cycle {update['iteration']}: Draft generated.")
                    status_box.info(f"Cycle {update['iteration']}: Lesson drafted ({len(update['markdown'].split())} words).")

                elif step == "EVALUATED":
                    progress_bar.progress(70, text=f"Cycle {update['iteration']}: Evaluation completed.")
                    eval_out = update["evaluation"]
                    cycles_data.append({
                        "iteration": update["iteration"],
                        "score": update["score"],
                        "passed": update["passed"],
                        "evaluation": eval_out,
                        "markdown": workflow.current_markdown,
                    })

                elif step == "REGENERATING":
                    progress_bar.progress(85, text=f"Surgically regenerating draft based on evaluator feedback...")
                    status_box.warning("Feedback fed back to generator. Applying surgical fixes...")

                elif step == "COMPLETE":
                    progress_bar.progress(100, text="Workflow complete!")
                    st.session_state.workflow_history = {
                        "topic": topic,
                        "is_approved": update["is_approved"],
                        "final_score": update["final_score"],
                        "cycles": cycles_data,
                        "rejection_log": update["rejection_log"],
                        "final_markdown": update["lesson_markdown"],
                    }

    # Render results if available
    history = st.session_state.workflow_history

    tab_exec, tab_lesson, tab_rejections, tab_memory = st.tabs(
        ["📊 Live Workflow Execution", "📄 Shippable Lesson", "📋 Rejection Audit Log", "🧠 Evolving Memory"]
    )

    with tab_exec:
        if not history:
            st.write("👈 Configure topic and click **'Run Quality-Gate Generator'** in the sidebar to begin.")
        else:
            # Banner
            if history["is_approved"]:
                st.success(f"🎉 **APPROVED & CLEARED FOR SHIPPING!** Final Score: **{history['final_score']}/11**")
            else:
                st.error(f"⛔ **TERMINATED WITHOUT APPROVAL:** Reached maximum retries. Final Score: **{history['final_score']}/11**")

            # Cycle tabs
            cycle_tabs = st.tabs([f"Cycle {c['iteration']} (Score: {c['score']}/11)" for c in history["cycles"]])

            for i, c in enumerate(history["cycles"]):
                with cycle_tabs[i]:
                    eval_out = c["evaluation"]

                    col_m1, col_m2, col_m3 = st.columns(3)
                    with col_m1:
                        st.metric("Total Score", f"{c['score']}/11")
                    with col_m2:
                        st.metric("Status", eval_out.overall_status)
                    with col_m3:
                        st.metric("Recommendation", eval_out.final_recommendation)

                    st.markdown("### 📋 11-Rubric Pass/Fail Checkpoints")

                    for r in eval_out.rubric_results:
                        with st.expander(f"{'✅' if r.score == 1 else '❌'} Rubric {r.rubric_id}: {r.rubric_name} — {r.status}"):
                            st.markdown(f"**Evidence / Quoted Text:**\n> {r.evidence}")
                            if r.score == 0:
                                st.error(f"**Failure Reason:** {r.failure_reason}")
                                st.info(f"**Actionable Fix Required:** {r.suggested_fix}")

                    st.markdown("### 📝 Draft Snapshot for this Cycle")
                    with st.expander(f"View Raw Draft for Cycle {c['iteration']}"):
                        st.code(c["markdown"], language="markdown")

    with tab_lesson:
        lesson_file = FINAL_OUTPUT_DIR / "RAG_Lesson.md"
        if lesson_file.exists():
            with open(lesson_file, "r", encoding="utf-8") as f:
                content = f.read()
            st.markdown(content)
            st.download_button("📥 Download Shippable Lesson (.md)", data=content, file_name="RAG_Lesson.md", mime="text/markdown")
        else:
            st.info("No approved lesson generated yet. Run the workflow to produce the lesson.")

    with tab_rejections:
        rejection_file = FINAL_OUTPUT_DIR / "Rejection_Log.md"
        if rejection_file.exists():
            with open(rejection_file, "r", encoding="utf-8") as f:
                log_content = f.read()
            st.markdown(log_content)
            st.download_button("📥 Download Rejection Log (.md)", data=log_content, file_name="Rejection_Log.md", mime="text/markdown")
        else:
            st.info("No rejection log generated yet.")

    with tab_memory:
        st.subheader("🧠 Persistent Cross-Run Memory & Self-Evolution")
        mem_data = memory_store.load()

        col1, col2, col3 = st.columns(3)
        col1.metric("Total System Runs", mem_data.get("total_runs", 0))
        col2.metric("Approved Runs", mem_data.get("successful_runs", 0))
        col3.metric("Rejected / Terminated Runs", mem_data.get("failed_runs", 0))

        st.markdown("### 🛡️ Dynamic Negative Constraints (Learned from Past Failures)")
        st.caption("These constraints are dynamically injected into the generator prompt before generation to prevent repeating past mistakes.")
        for rule in mem_data.get("learned_negative_constraints", []):
            st.markdown(f"- ⚠️ **{rule}**")

        st.markdown("### 📉 Recurring Failure Frequencies")
        freqs = mem_data.get("recurring_failures", {})
        if freqs:
            st.json(freqs)
        else:
            st.info("No recurring failure spikes recorded yet.")


if __name__ == "__main__":
    main()
