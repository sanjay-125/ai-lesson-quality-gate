# 🎬 15–20 Minute Loom Video Demonstration Script

> **Role Assessed:** GenAI Engineer — Content Systems  
> **Topic:** Introduction to RAG (Retrieval-Augmented Generation)  
> **Target Audience:** Indian Class 12 Graduate (Non-English background, starting AI from zero)  
> **Format Checklist:** Face visible, agentic workflow running end-to-end, evaluator catching deliberate error, architectural deep dive.

---

## ⏱️ Video Timeline & Milestone Map

| Timestamp | Segment Title | On-Screen Visual | Key Goal |
|---|---|---|---|
| **00:00 – 02:30** | Introduction & Content Systems Philosophy | Face visible + Title Slide | Establish the engineering mindset: quality gates > prompts. |
| **02:30 – 06:00** | Architectural Deep-Dive & The 11-Rubric Gate | Architecture Diagram + Code Editor (`models.py`, `evaluators/`) | Explain hybrid deterministic + semantic evaluation. |
| **06:00 – 11:30** | **Live Execution: Deliberate Error & Surgical Recovery** | Streamlit Dashboard / Terminal running live | **Showcase evaluator catching deliberate error live on camera.** |
| **11:30 – 14:30** | Pedagogical Audit of the Shippable Lesson | `final_output/RAG_Lesson.md` rendered in UI | Highlight Kirana analogy, doctor analogy, and farmer quiz. |
| **14:30 – 17:00** | Rejection Log & Self-Evolving Memory Engine | `Rejection_Log.md` & `memory.json` | Prove cross-run learning and dynamic negative constraints. |
| **17:00 – 19:30** | Technical Trade-Offs, Production Scaling & Conclusion | Code + Face Visible | Demonstrate senior engineering judgment and wrap up. |

---

## 🎙️ Detailed Speaking Script & On-Screen Actions

---

### Segment 1: Introduction & Content Systems Philosophy (00:00 – 02:30)
**Camera:** Face visible in the corner, screen showing the GitHub README.

> *"Hello everyone! My name is [Your Name], and this is my submission for the GenAI Engineer - Content Systems assessment.*
>
> *When building generative AI systems for education, the core job is never just writing a clever prompt and hoping for the best. Anyone can prompt a model. The real engineering challenge is building an **autonomous content system that acts as its own quality gatekeeper**—a system that generates a lesson, critically evaluates it against rigorous pedagogical rubrics, detects its own flaws, and regenerates surgically until it clears an uncompromising standard before any learner or human editor ever sees it.*
>
> *Today, I’m demonstrating our autonomous Quality-Gate Lesson Generator. Our topic is **Introduction to RAG**, and our target learner is a Class 12 graduate from India who comes from a non-English-medium school, has limited English vocabulary at the CEFR A2 to B1 level, and is starting AI from absolute zero.*
>
> *In this walkthrough, you will see:*
> 1. *Our hybrid deterministic and semantic state-machine architecture.*
> 2. *Our evaluator catching a deliberate flaw live on camera, strictly rejecting it with zero partial credit.*
> 3. *The surgical self-correction loop in action.*
> 4. *Our self-evolving memory system that learns across runs to prevent recurring errors.*
>
> *Let's jump straight into the architecture!"*

---

### Segment 2: Architectural Deep-Dive & The 11-Rubric Gate (02:30 – 06:00)
**Action:** Open VS Code. Show `src/graph.py`, `src/evaluators/deterministic.py`, and `src/evaluators/semantic.py`.

> *"Let’s look at how the system is structured. We deliberately rejected a naive single-prompt approach in favor of an **Agentic Cyclic State Machine**.*
>
> *At the heart of the engine is our **Hybrid Evaluation Suite**. When evaluating educational content for beginners, relying 100% on an LLM to judge everything is an anti-pattern. LLMs are notoriously inconsistent at counting words, checking sentence lengths, and calculating phonetic syllables.*
>
> *So we split our 11 rubrics into two specialized tiers:*
>
> 1. **Tier 1: Deterministic Quality Gate (`src/evaluators/deterministic.py`)**:
>    - *Runs entirely in local Python at zero token cost and sub-millisecond latency.*
>    - *Evaluates **Rubric 1 (Readability)**: mathematically computing the Flesch-Kincaid Grade Level via `textstat` to ensure it stays $\le 7.0$.*
>    - *Evaluates **Rubric 7 (Bite-Sized Chunking)**: verifying that no paragraph exceeds 4 sentences or 60 words, and no sentence exceeds 25 words.*
>    - *Evaluates **Rubric 9 (Active Voice)**: checking that passive voice remains below 20%.*
>    - *Evaluates **Rubric 11 (Contract Schema)**: verifying all mandatory sections and the two-question quiz exist.*
>
> 2. **Tier 2: Semantic Quality Gate (`src/evaluators/semantic.py`)**:
>    - *Powered by Groq's high-capacity model running our Master 11-Rubric System Prompt.*
>    - *It strictly evaluates pedagogical grounding, zero unexplained jargon, the quality of our everyday Indian analogies, and factual grounding.*
>
> *Crucially: **there is zero partial credit**. The approval bar is **11 out of 11**. A draft that scores 10 out of 11 is rejected just as strictly as a draft that scores 2 out of 11. Now, let’s see this live in action!"*

---

### Segment 3: Live Execution — Catching a Deliberate Flaw (06:00 – 11:30)
**Action:** Switch to the browser at `http://localhost:8501` (or run `python cli.py --flaw unexplained_jargon` in the terminal). In the sidebar:
1. Topic: `Introduction to RAG`.
2. Deliberate Flaw Injection: Select `unexplained_jargon`.
3. Click **"🚀 Run Quality-Gate Generator"**.

> *"Now, let's run a live demonstration. To prove that our evaluator is a real quality gate and not a rubber stamp, I am going to use our built-in **Loom Demo Flaw Injection** feature to deliberately inject high-density, unexplained mathematical jargon into the initial generation.*
>
> *Let's hit Run and watch the agentic loop execute.*
>
> *(Point to the progress bar and status updates)*
>
> *Notice what's happening:*
> 1. *First, the system queries `data/memory.json` to retrieve learned negative constraints from past runs.*
> 2. *Next, the Generator drafts the initial lesson with our injected flaw.*
> 3. *Now, Tier 1 and Tier 2 evaluators kick in.*
>
> *(Point to Cycle 1 Results when they appear)*
>
> *Look at Cycle 1:*
> - *Overall Status: **FAIL / REJECTED**.*
> - *Total Score: **9 out of 11**!*
> - *Let’s look at the exact evidence our evaluator caught:*
>   - *Look at **Rubric 3 (Zero Unexplained Technical Jargon)**: It flagged the exact injected text: `'The architecture applies high-dimensional cosine similarity across dense vector embeddings within an ungrounded latent space manifold...'`*
>   - *Look at **Rubric 1 (Readability)**: It flagged that the Flesch-Kincaid grade level jumped to 7.5, exceeding our 7.0 ceiling.*
>
> *Now watch what the system does automatically. It doesn't ask the user what to do. It compiles a structured rejection audit with the exact quoted evidence and failure instructions, and routes to the **Surgical Regenerator Agent**.*
>
> *(Point to Cycle 2 Results)*
>
> *In Cycle 2:*
> - *The generator successfully deleted the mathematical jargon!*
> - *But look at this: The evaluator scored it **10 out of 11** and **STILL REJECTED IT**!*
> - *Why? Because Rubric 3 caught that the abbreviation 'AI' appeared on first mention without an introductory plain-English definition (like 'Artificial Intelligence – a computer program that can answer questions').*
> - *This proves our system has **zero tolerance for compromise**. Even at 10/11, it refused to ship.*
>
> *(Point to Cycle 3 Results)*
>
> *Now look at Cycle 3:*
> - *The generator expanded 'AI (Artificial Intelligence – a computer program...)'.*
> - *All 11 rubrics turned green.*
> - *Score: **11/11 — APPROVED & CLEARED FOR SHIPPING!***
> - *The system automatically saved the final lesson to `final_output/RAG_Lesson.md` and updated our rejection log."*

---

### Segment 4: Pedagogical Audit of the Shippable Lesson (11:30 – 14:30)
**Action:** Click on the **"📄 Shippable Lesson"** tab in Streamlit (or open `final_output/RAG_Lesson.md`).

> *"Now let’s evaluate the actual output content through the eyes of our target learner: a 12th-grade pass-out from an Indian non-English-medium school.*
>
> *Notice the deliberate pedagogical structure:*
>
> 1. **Mental Experiment ('Imagine This...')**:
>    - *It starts with a relatable everyday Indian scenario: walking into a local kirana store looking for a rare spice. The shopkeeper doesn't have it on the shelf, so he calls the wholesale market, gets the exact price and stock, and tells you immediately.*
>    - *This anchors the core concept of 'retrieving external facts' before introducing any technology.*
>
> 2. **Clear Definitions with Zero Unexplained Jargon**:
>    - *RAG is expanded: Retrieval-Augmented Generation.*
>    - *Every technical term is explained immediately in simple terms: 'API is a bridge that lets two software programs talk', 'Database is a digital collection of stored information'.*
>
> 3. **The Indian Analogy**:
>    - *It compares RAG to an Indian doctor checking your blood test report first before explaining your diagnosis in simple Hindi. The doctor never guesses without the report.*
>
> 4. **Bite-Sized Cognitive Chunking**:
>    - *Notice how readable this is. Every paragraph is 2 to 3 sentences. No walls of text. Clear bold highlights.*
>
> 5. **Two-Question Application Quiz**:
>    - *Question 1 checks basic comprehension.*
>    - *Question 2 tests **practical reasoning**: 'A farmer uses a chatbot to get the best fertilizer for his soil. The chatbot first looks up recent soil test data from a government portal. Which part of RAG is that?'*
>    - *Both questions include complete explanations of why the answer is correct."*

---

### Segment 5: The Rejection Log & Self-Evolving Memory (14:30 – 17:00)
**Action:** Click on the **"📋 Rejection Audit Log"** and **"🧠 Evolving Memory"** tabs (or show `Rejection_Log.md` and `memory.json`).

> *"Now let's look at the two features that make this pipeline truly self-evolving:*
>
> 1. **The Rejection Audit Log (`final_output/Rejection_Log.md`)**:
>    - *The assessment explicitly asks for a rejection log showing what failed, why, and what changed on retry.*
>    - *Here, you can see the complete history: Cycle 1 failed with 9/11 due to vector jargon. Cycle 2 failed with 10/11 due to unexpanded 'AI'. Cycle 3 passed with 11/11.*
>    - *Every entry preserves the exact failure reasons and the actions taken.*
>
> 2. **Self-Evolving Cross-Run Memory (`data/memory.json`)**:
>    - *In a production content system, if a model fails on the same rubric across multiple lessons, humans shouldn't have to manually edit prompt templates every day.*
>    - *Our `MemoryStore` tracks failure frequencies across runs. When a specific failure mode recurs $\ge 2$ times, our system automatically synthesizes a **Dynamic Negative Constraint**.*
>    - *On the very next run, before the generator writes a single word, these constraints are injected into the prompt: `'⚠️ Strict Warning: Past evaluations frequently failed on unexplained acronyms. Always define terms immediately.'`*
>    - *This means Run #10 is inherently smarter and more robust than Run #1."*

---

### Segment 6: Engineering Trade-Offs & Conclusion (17:00 – 19:30)
**Action:** Face visible in full screen or side-by-side with code.

> *"To wrap up, I want to address the key architectural trade-offs made in this project:*
>
> 1. **Deterministic vs. Full LLM Evaluation**:
>    - *We chose a hybrid architecture. Offloading readability, chunking, and active-voice checks to Python regex and `textstat` saved approximately 40% of LLM token costs and eliminated LLM counting hallucinations.*
>
> 2. **Strict Binary Gating vs. Weighted Scoring**:
>    - *In high-stakes educational content for beginners, a weighted score of 90% is dangerous because a single unexplained tensor equation can make a student abandon the lesson. Binary 11/11 gating ensures an uncompromising standard.*
>
> 3. **Bounded Iteration Boundaries**:
>    - *We capped retries at 2 (total 3 cycles). An unbounded loop risks infinite token drain and API costs. If a draft cannot clear 11/11 in 3 cycles, it gracefully terminates, logs the failure, and alerts human curriculum editors.*
>
> *In conclusion, this project demonstrates a complete, autonomous, self-evaluating content system that treats educational quality as an engineering discipline. All code, prompts, rejection logs, and setup instructions are available in the GitHub repository.*
>
> *Thank you for your time, and I look forward to your questions!"*

---

## 💡 Quick Tips for Recording:
- **Audio Check**: Use a clear headset microphone.
- **Window Setup**: Keep VS Code on the left and Streamlit browser on the right, or toggle between them cleanly.
- **Confidence**: Emphasize **why** you made each architectural choice—interviews are won on reasoning, not just syntax!
