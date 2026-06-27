from google import genai
import streamlit as st
import json
import re

# ──────────────────────────────────────────────────────────────────────────────
# PAGE CONFIG  (must be first Streamlit call)
# ──────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="A-Level StudyBot",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ──────────────────────────────────────────────────────────────────────────────
# CURRICULUM DATA
# ──────────────────────────────────────────────────────────────────────────────
SUBJECTS: dict[str, list[str]] = {
    "Biology": [
        "Cell Structure & Function", "Biological Molecules", "Enzymes",
        "Cell Membranes & Transport", "Mitosis & Meiosis", "DNA & Protein Synthesis",
        "Genetic Inheritance", "Ecology & Population", "Homeostasis",
        "Nervous System & Hormones", "Immunity & Disease", "Plant Biology",
        "Biodiversity & Classification", "Natural Selection & Evolution",
    ],
    "Chemistry": [
        "Atomic Structure", "Amount of Substance (Moles)", "Chemical Bonding",
        "Energetics & Thermochemistry", "Kinetics & Reaction Rates", "Equilibria (Le Chatelier)",
        "Redox Reactions", "Group 2 & Group 7 Elements", "Organic Chemistry Basics",
        "Alcohols & Halogenoalkanes", "Carbonyl Compounds", "Acids, Bases & pH",
        "Electrochemistry", "Transition Metals & Coordination Compounds", "Polymers",
    ],
    "Physics": [
        "Measurements & Uncertainties", "Kinematics (SUVAT)", "Newton's Laws & Dynamics",
        "Forces, Moments & Equilibrium", "Work, Energy & Power", "Waves & Superposition",
        "Quantum Physics & Photoelectric Effect", "Electricity & Circuits",
        "Magnetic Fields & Electromagnetic Induction", "Nuclear Physics & Radioactivity",
        "Thermal Physics & Ideal Gases", "Circular Motion & Gravitational Fields",
        "Electric Fields & Capacitance",
    ],
    "Mathematics": [
        "Algebra & Functions", "Coordinate Geometry", "Sequences & Series",
        "Trigonometry", "Differentiation", "Integration",
        "Exponentials & Logarithms", "Proof by Contradiction & Induction",
        "Vectors", "Probability & Statistics", "Mechanics (Kinematics & Forces)",
        "Numerical Methods", "Complex Numbers",
    ],
    "Economics": [
        "Supply, Demand & Elasticity", "Market Structures (Perfect to Monopoly)",
        "Market Failure & Externalities", "Government Intervention & Policy",
        "National Income & GDP", "Inflation", "Unemployment",
        "International Trade & Comparative Advantage", "Exchange Rates",
        "Fiscal & Monetary Policy", "Economic Growth & Business Cycle",
        "Development Economics",
    ],
    "Computer Science": [
        "Data Types & Binary Representation", "Boolean Logic & Logic Gates",
        "Algorithm Design & Analysis", "Data Structures (Lists, Trees, Graphs)",
        "Programming Paradigms (OOP, Functional)", "Computer Architecture & Fetch-Execute",
        "Operating Systems & Scheduling", "Networking & TCP/IP",
        "Databases & SQL", "Cybersecurity & Encryption",
        "Computational Thinking & Turing Machines",
    ],
    "History": [
        "Causes & Outbreak of World War I", "The Western Front & Trench Warfare",
        "Treaty of Versailles & Its Impact", "Rise of Nazism in Germany",
        "Causes of World War II", "Cold War Origins & Superpower Rivalry",
        "The Cuban Missile Crisis", "Decolonisation in Africa & Asia",
    ],
    "Psychology": [
        "Research Methods & Ethics", "Biopsychology & Brain Structure",
        "Social Influence (Conformity & Obedience)", "Memory Models",
        "Attachment Theory", "Psychopathology (OCD, Phobias, Depression)",
        "Approaches: Behaviourist, Cognitive, Biological, Psychodynamic",
    ],
}

EXAM_BOARDS: dict[str, dict] = {
    "CAIE (Cambridge)": {
        "style": (
            "Use CAIE command words precisely: 'state' (recall only), 'describe' (what happens, no why), "
            "'explain' (mechanism/reason required), 'outline' (brief explanation), 'discuss' (pros, cons, evidence), "
            "'evaluate' (judgement with justification). Questions should mirror CAIE paper style."
        ),
    },
    "Edexcel": {
        "style": (
            "Use point-evidence-explain structure. Extended questions require a clear argument with "
            "evaluative conclusions. Command words: 'analyse', 'assess', 'evaluate', 'justify'."
        ),
    },
    "AQA": {
        "style": (
            "Mark scheme uses bullet-point credit points. Synoptic links between topics are rewarded. "
            "Extended answer marking uses levels of response (Level 1–3). Command words: 'explain', 'assess', 'evaluate'."
        ),
    },
    "OCR": {
        "style": (
            "Extended answers use levels of response marking. Questions often require application to novel "
            "contexts. Command words: 'describe', 'explain', 'evaluate', 'compare'."
        ),
    },
}

DIFFICULTIES: dict[str, str] = {
    "Foundation (E-D)":   "basic recall and understanding; single-mark statements; no application required",
    "Intermediate (C-B)": "understanding with some application; 2–4 mark explanations; cause-and-effect reasoning",
    "Advanced (A)":       "analysis and multi-step reasoning; application to novel contexts; expect 4–8 mark explanations",
    "Exam Standard (A*)": "highest-order A-level questions: synoptic links, evaluation with justification, extended analysis",
}

QUESTION_TYPES: dict[str, str] = {
    "Multiple Choice (MCQ)":         "mcq",
    "Short Answer (1–4 marks)":      "short",
    "Structured (4–9 marks)":        "structured",
    "Mixed (all types)":             "mixed",
}

GRADE_THRESHOLDS = [
    ("A*", 90), ("A", 80), ("B", 70), ("C", 60), ("D", 50), ("E", 40), ("U", 0)
]

# ──────────────────────────────────────────────────────────────────────────────
# SESSION STATE INITIALISATION
# ──────────────────────────────────────────────────────────────────────────────
def init_state() -> None:
    defaults = {
        "view":          "home",   # home | quiz | results
        "questions":     [],
        "current_q":     0,
        "answers":       {},       # {idx: answer_str}
        "feedback":      {},       # {idx: feedback_dict}
        "total_score":   0,
        "total_marks":   0,
        "streak":        0,
        "max_streak":    0,
        "quiz_config":   {},
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


# ──────────────────────────────────────────────────────────────────────────────
# GOOGLE CLIENT  — cached so we don't recreate on every rerun
# ──────────────────────────────────────────────────────────────────────────────
@st.cache_resource
def get_client():
    return genai.Client(
        api_key=st.secrets["GEMINI_API_KEY"]
    )


# ──────────────────────────────────────────────────────────────────────────────
# API HELPERS
# ──────────────────────────────────────────────────────────────────────────────
def _strip_json_fences(text: str) -> str:
    """Remove markdown code fences the model might wrap around JSON."""
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    return text.strip()


def generate_questions(
    subject: str, topic: str, exam_board: str,
    q_type: str, difficulty: str, num_q: int
) -> list[dict]:
    client = get_client()

    type_instruction = {
        "mcq":        f"All {num_q} questions must be multiple-choice with exactly 4 options (A–D). marks = 1 each.",
        "short":      f"All {num_q} questions are short-answer worth 2–4 marks each.",
        "structured": f"All {num_q} questions are structured worth 5–9 marks each.",
        "mixed":      f"Mix of MCQ (marks=1), short (marks=2-4), and structured (marks=5-9) across the {num_q} questions.",
    }[q_type]

    prompt = f"""You are an expert A-level examiner writing questions for {exam_board}.
Subject: {subject}
Topic: {topic}
Difficulty: {difficulty} — {DIFFICULTIES[difficulty]}
Board style: {EXAM_BOARDS[exam_board]['style']}

Generate exactly {num_q} questions. {type_instruction}

Return ONLY a valid JSON object — no markdown fences, no commentary, no trailing text:
{{
  "questions": [
    {{
      "id": 1,
      "type": "mcq" | "short" | "structured",
      "marks": <integer>,
      "question": "<full question text>",
      "options": {{"A": "...", "B": "...", "C": "...", "D": "..."}} (MCQ only — omit for short/structured),
      "correct_option": "A" | "B" | "C" | "D" (MCQ only — omit for short/structured),
      "mark_scheme": ["Point 1 — 1 mark", "Point 2 — 1 mark", ...] (one entry per mark),
      "model_answer": "<complete model answer worthy of full marks>"
    }}
  ]
}}

Rules:
- mark_scheme MUST have exactly <marks> entries.
- model_answer must clearly demonstrate all mark scheme points.
- Questions must be genuinely challenging for {difficulty}.
- Use the exact command words appropriate for {exam_board}."""

    resp = client.models.generate_content(
    model="gemini-2.5-flash",
    contents=prompt,
)

    raw = _strip_json_fences(resp.text)
    data = json.loads(raw)
    return data["questions"]


def evaluate_answer(q: dict, student_answer: str) -> dict:
    """AI marks a short/structured answer and returns structured feedback."""
    client = get_client()

    prompt = f"""You are a strict but fair A-level examiner. Mark this student answer against the mark scheme.

Question ({q['marks']} marks): {q['question']}

Mark scheme:
{json.dumps(q['mark_scheme'], indent=2)}

Student answer: {student_answer}

Return ONLY valid JSON — no fences, no extra text:
{{
  "marks_awarded": <integer 0–{q['marks']}>,
  "marks_hit":   ["Exact mark scheme point awarded", ...],
  "marks_missed":["Exact mark scheme point NOT awarded", ...],
  "feedback":    "<2–3 sentences: what was strong, what was missing>",
  "model_answer":"{q.get('model_answer', '')}",
  "tip":         "<one specific, actionable improvement tip>"
}}

Rules:
- marks_hit + marks_missed must together list ALL mark scheme points.
- Be strict: vague or imprecise answers do not earn marks.
- marks_awarded must equal len(marks_hit)."""

    resp = client.models.generate_content(
    model="gemini-2.5-flash",
    contents=prompt,
)

    raw = _strip_json_fences(resp.text)
    return json.loads(raw)


# ──────────────────────────────────────────────────────────────────────────────
# UTILITY
# ──────────────────────────────────────────────────────────────────────────────
def get_grade(pct: float) -> str:
    for grade, threshold in GRADE_THRESHOLDS:
        if pct >= threshold:
            return grade
    return "U"


def grade_color(grade: str) -> str:
    return {
        "A*": "#f8d64e", "A": "#00b894", "B": "#0984e3",
        "C": "#fdcb6e",  "D": "#e17055", "E": "#e17055", "U": "#d63031",
    }.get(grade, "#636e72")


# ──────────────────────────────────────────────────────────────────────────────
# CUSTOM CSS
# ──────────────────────────────────────────────────────────────────────────────
CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Manrope:wght@300;400;500;600;700;800&family=Inter:wght@300;400;500;600&family=JetBrains+Mono:wght@400;500&display=swap');

/* ── Root palette ── */
:root {
    --bg:           #0d0e17;
    --surface:      #161726;
    --card:         #1c1d30;
    --card-hover:   #21223a;
    --border:       #2a2b42;
    --accent:       #7c6af7;
    --accent-light: #a89ff7;
    --success:      #00b894;
    --warn:         #fdcb6e;
    --danger:       #d63031;
    --text:         #dfe6e9;
    --muted:        #636e72;
    --radius:       14px;
    --radius-sm:    8px;
}

/* ── Global ── */
*, *::before, *::after { box-sizing: border-box; }

.stApp {
    background: var(--bg);
    font-family: 'Inter', sans-serif;
    color: var(--text);
}

/* ── Hide Streamlit chrome ── */
header[data-testid="stHeader"]           { display: none !important; }
footer                                   { display: none !important; }
#MainMenu                                { display: none !important; }

/* ── Sidebar ── */
section[data-testid="stSidebar"] {
    background: var(--surface);
    border-right: 1px solid var(--border);
}
section[data-testid="stSidebar"] > div   { padding: 1.5rem 1.2rem; }

/* ── Main content ── */
.main .block-container {
    padding: 2rem 2.5rem 4rem;
    max-width: 820px;
}

/* ── Typography ── */
h1,h2,h3,h4 { font-family: 'Manrope', sans-serif !important; color: var(--text) !important; }

.logo-text {
    font-family: 'Manrope', sans-serif;
    font-size: 1.35rem;
    font-weight: 800;
    letter-spacing: -0.5px;
    background: linear-gradient(135deg, var(--accent), var(--accent-light));
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}
.logo-sub {
    font-size: 0.72rem;
    color: var(--muted);
    font-weight: 400;
    letter-spacing: 0.4px;
    margin-top: 1px;
}

/* ── Cards ── */
.q-card {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 1.75rem 1.75rem 1.5rem;
    margin-bottom: 1.5rem;
}

.feature-card {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 1.5rem;
    height: 100%;
    transition: border-color 0.2s;
}
.feature-card:hover { border-color: var(--accent); }

/* ── Question text ── */
.q-meta {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.7rem;
    color: var(--accent-light);
    letter-spacing: 1px;
    text-transform: uppercase;
    margin-bottom: 0.8rem;
}

.q-text {
    font-size: 1.05rem;
    line-height: 1.75;
    color: var(--text);
    margin-bottom: 1.25rem;
}

/* ── Marks pill ── */
.marks-pill {
    display: inline-flex;
    align-items: center;
    background: rgba(124,106,247,0.12);
    border: 1px solid rgba(124,106,247,0.25);
    color: var(--accent-light);
    padding: 2px 10px;
    border-radius: 50px;
    font-size: 0.72rem;
    font-weight: 600;
    font-family: 'JetBrains Mono', monospace;
    letter-spacing: 0.5px;
}

/* ── Feedback cards ── */
.fb-correct {
    background: rgba(0,184,148,0.08);
    border: 1px solid rgba(0,184,148,0.3);
    border-radius: var(--radius);
    padding: 1.25rem 1.5rem;
    margin-top: 1rem;
}
.fb-partial {
    background: rgba(253,203,110,0.06);
    border: 1px solid rgba(253,203,110,0.3);
    border-radius: var(--radius);
    padding: 1.25rem 1.5rem;
    margin-top: 1rem;
}
.fb-wrong {
    background: rgba(214,48,49,0.06);
    border: 1px solid rgba(214,48,49,0.3);
    border-radius: var(--radius);
    padding: 1.25rem 1.5rem;
    margin-top: 1rem;
}

/* ── Mark scheme points ── */
.point-hit   { color: var(--success); padding: 3px 0; font-size: 0.9rem; }
.point-miss  { color: #b2bec3; padding: 3px 0; font-size: 0.9rem; opacity: 0.6; text-decoration: line-through; }

/* ── Model answer block ── */
.model-ans {
    background: rgba(0,184,148,0.06);
    border-left: 3px solid var(--success);
    padding: 1rem 1.25rem;
    border-radius: 0 var(--radius-sm) var(--radius-sm) 0;
    color: #b2f0e0;
    font-size: 0.92rem;
    line-height: 1.65;
    margin-top: 0.5rem;
    white-space: pre-wrap;
}

/* ── Tip block ── */
.tip-block {
    background: rgba(253,203,110,0.06);
    border-left: 3px solid var(--warn);
    padding: 0.75rem 1.1rem;
    border-radius: 0 var(--radius-sm) var(--radius-sm) 0;
    color: #fde08d;
    font-size: 0.87rem;
    margin-top: 0.75rem;
}

/* ── Score display ── */
.score-pill {
    background: rgba(124,106,247,0.15);
    border: 1px solid rgba(124,106,247,0.3);
    border-radius: 50px;
    padding: 4px 14px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.8rem;
    color: var(--accent-light);
    display: inline-block;
}

/* ── Streak ── */
.streak-chip {
    font-size: 0.8rem;
    color: #fdcb6e;
    font-weight: 600;
}

/* ── Grade circle on results ── */
.grade-circle {
    width: 100px;
    height: 100px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-family: 'Manrope', sans-serif;
    font-size: 2.5rem;
    font-weight: 800;
    margin: 0 auto 1rem;
}

/* ── Sidebar stat boxes ── */
.stat-box {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: var(--radius-sm);
    padding: 0.65rem 0.9rem;
    margin-bottom: 0.5rem;
    display: flex;
    align-items: center;
    justify-content: space-between;
}
.stat-label { color: var(--muted); font-size: 0.78rem; }
.stat-value { color: var(--text); font-weight: 700; font-size: 0.92rem; font-family: 'JetBrains Mono', monospace; }

/* ── Buttons ── */
.stButton > button {
    background: linear-gradient(135deg, #7c6af7, #6a5af7) !important;
    color: #fff !important;
    border: none !important;
    border-radius: var(--radius-sm) !important;
    font-weight: 600 !important;
    font-family: 'Inter', sans-serif !important;
    padding: 0.55rem 1.2rem !important;
    transition: opacity 0.15s, transform 0.1s !important;
    width: 100%;
}
.stButton > button:hover {
    opacity: 0.88 !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 6px 20px rgba(124,106,247,0.35) !important;
}

/* Secondary button pattern (wrap in .btn-ghost div) */
.btn-ghost .stButton > button {
    background: transparent !important;
    border: 1px solid var(--border) !important;
    color: var(--muted) !important;
}

/* ── Selectbox / radio / text area ── */
.stSelectbox > div > div,
.stTextArea textarea {
    background: var(--card) !important;
    border: 1px solid var(--border) !important;
    color: var(--text) !important;
    border-radius: var(--radius-sm) !important;
    font-family: 'Inter', sans-serif !important;
}
.stSelectbox label, .stTextArea label, .stSlider label, .stRadio label {
    color: var(--muted) !important;
    font-size: 0.82rem !important;
    font-weight: 500 !important;
}
.stRadio > div { gap: 0.4rem; }

/* Progress bar */
.stProgress > div > div > div > div {
    background: linear-gradient(90deg, var(--accent), var(--accent-light)) !important;
}

/* Divider */
hr { border-color: var(--border) !important; }

/* Expander */
details { border-radius: var(--radius-sm) !important; }

/* Alerts */
.stSuccess, .stInfo, .stWarning, .stError {
    border-radius: var(--radius-sm) !important;
}

/* ── Home hero ── */
.hero {
    text-align: center;
    padding: 3rem 0 2rem;
}
.hero-title {
    font-family: 'Manrope', sans-serif;
    font-size: 3rem;
    font-weight: 800;
    letter-spacing: -1.5px;
    background: linear-gradient(135deg, #dfe6e9, var(--accent-light));
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 0.5rem;
    line-height: 1.1;
}
.hero-sub {
    color: var(--muted);
    font-size: 1rem;
    margin-bottom: 1.5rem;
}

/* ── Result grade boundary bar ── */
.boundary-item {
    padding: 0.4rem 0.2rem;
    text-align: center;
    border-radius: var(--radius-sm);
    font-size: 0.78rem;
    font-weight: 600;
}
</style>
"""

# ──────────────────────────────────────────────────────────────────────────────
# SIDEBAR
# ──────────────────────────────────────────────────────────────────────────────
def render_sidebar() -> None:
    with st.sidebar:
        st.markdown('<div class="logo-text">🎓 StudyBot</div>', unsafe_allow_html=True)
        st.markdown('<div class="logo-sub">A-Level Exam Prep · AI-Powered</div>', unsafe_allow_html=True)
        st.divider()

        # ── Live session stats ──
        if st.session_state.total_marks > 0:
            pct = st.session_state.total_score / st.session_state.total_marks * 100
            grade = get_grade(pct)
            g_col = grade_color(grade)

            st.markdown(
                f'<div class="stat-box"><span class="stat-label">Score</span>'
                f'<span class="stat-value">{st.session_state.total_score}/{st.session_state.total_marks}</span></div>',
                unsafe_allow_html=True,
            )
            st.markdown(
                f'<div class="stat-box"><span class="stat-label">Grade</span>'
                f'<span class="stat-value" style="color:{g_col};">{grade}</span></div>',
                unsafe_allow_html=True,
            )
            if st.session_state.streak > 1:
                st.markdown(
                    f'<div class="stat-box"><span class="stat-label">Streak</span>'
                    f'<span class="stat-value streak-chip">🔥 {st.session_state.streak}</span></div>',
                    unsafe_allow_html=True,
                )
            st.progress(pct / 100)
            st.divider()

        # ── Setup controls ──
        st.markdown("**Setup**")

        subject   = st.selectbox("Subject", list(SUBJECTS.keys()), key="cfg_subject")
        topic     = st.selectbox("Topic",   SUBJECTS[subject],     key="cfg_topic")
        board     = st.selectbox("Exam Board", list(EXAM_BOARDS.keys()), key="cfg_board")
        diff      = st.selectbox("Difficulty", list(DIFFICULTIES.keys()), key="cfg_diff")
        q_type    = st.selectbox("Question Type", list(QUESTION_TYPES.keys()), key="cfg_qtype")
        num_q     = st.slider("Questions", 3, 15, 5, key="cfg_numq")

        st.markdown("<br>", unsafe_allow_html=True)

        if st.button("▶  Generate Questions", use_container_width=True):
            _do_generate(subject, topic, board, diff, q_type, num_q)

        if st.session_state.questions:
            st.markdown('<div class="btn-ghost">', unsafe_allow_html=True)
            if st.button("↺  Reset Session", use_container_width=True):
                _reset()
            st.markdown("</div>", unsafe_allow_html=True)


def _do_generate(subject, topic, board, diff, q_type_label, num_q) -> None:
    q_type_val = QUESTION_TYPES[q_type_label]
    with st.spinner(f"Generating {num_q} questions on {topic}…"):
        try:
            questions = generate_questions(subject, topic, board, q_type_val, diff, num_q)
        except json.JSONDecodeError as e:
            st.error(f"API returned invalid JSON. Try again. ({e})")
            return
        except Exception as e:
            st.error(f"Generation failed: {e}")
            return

    # Reset quiz state
    st.session_state.questions   = questions
    st.session_state.current_q   = 0
    st.session_state.answers     = {}
    st.session_state.feedback    = {}
    st.session_state.total_score = 0
    st.session_state.total_marks = 0
    st.session_state.streak      = 0
    st.session_state.max_streak  = 0
    st.session_state.view        = "quiz"
    st.session_state.quiz_config = {
        "subject": subject, "topic": topic, "board": board,
        "diff": diff, "q_type_label": q_type_label, "num_q": num_q,
    }
    st.rerun()


def _reset() -> None:
    for k in ["questions","current_q","answers","feedback","total_score",
              "total_marks","streak","max_streak","view","quiz_config"]:
        if k in st.session_state:
            del st.session_state[k]
    st.rerun()


# ──────────────────────────────────────────────────────────────────────────────
# VIEW: HOME
# ──────────────────────────────────────────────────────────────────────────────
def render_home() -> None:
    st.markdown("""
    <div class="hero">
        <div class="hero-title">Study Smarter.<br>Grade Higher.</div>
        <div class="hero-sub">AI-generated questions · Real mark scheme grading · Cambridge · Edexcel · AQA · OCR</div>
    </div>
    """, unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("""<div class="feature-card">
            <div style="font-size:1.8rem;margin-bottom:.6rem;">🧠</div>
            <div style="font-weight:700;font-family:'Manrope',sans-serif;font-size:1rem;margin-bottom:.4rem;color:#dfe6e9;">Exam-Board Accurate</div>
            <div style="color:#636e72;font-size:.85rem;line-height:1.5;">Questions calibrated to your exact board's command words and mark scheme structure.</div>
        </div>""", unsafe_allow_html=True)
    with c2:
        st.markdown("""<div class="feature-card">
            <div style="font-size:1.8rem;margin-bottom:.6rem;">✅</div>
            <div style="font-weight:700;font-family:'Manrope',sans-serif;font-size:1rem;margin-bottom:.4rem;color:#dfe6e9;">Real-Time Marking</div>
            <div style="color:#636e72;font-size:.85rem;line-height:1.5;">Answers graded point-by-point against the mark scheme with specific feedback on what you missed.</div>
        </div>""", unsafe_allow_html=True)
    with c3:
        st.markdown("""<div class="feature-card">
            <div style="font-size:1.8rem;margin-bottom:.6rem;">📈</div>
            <div style="font-weight:700;font-family:'Manrope',sans-serif;font-size:1rem;margin-bottom:.4rem;color:#dfe6e9;">Live Grade Tracking</div>
            <div style="color:#636e72;font-size:.85rem;line-height:1.5;">Running score, letter grade, and streak counter update as you go.</div>
        </div>""", unsafe_allow_html=True)

    st.markdown(
        '<p style="color:var(--muted);text-align:center;margin-top:2.5rem;font-size:.9rem;">'
        '← Configure your session in the sidebar, then hit <strong style="color:#dfe6e9;">Generate Questions</strong>.'
        "</p>",
        unsafe_allow_html=True,
    )


# ──────────────────────────────────────────────────────────────────────────────
# VIEW: QUIZ
# ──────────────────────────────────────────────────────────────────────────────
def render_quiz() -> None:
    questions   = st.session_state.questions
    idx         = st.session_state.current_q

    # Guard: if all questions done, go to results
    if idx >= len(questions):
        st.session_state.view = "results"
        st.rerun()
        return

    q             = questions[idx]
    answered      = idx in st.session_state.answers
    q_type        = q.get("type", "short")
    marks         = q.get("marks", 1)
    total_q       = len(questions)
    cfg           = st.session_state.quiz_config

    # ── Header row ──
    col_prog, col_score, col_streak = st.columns([3, 1.2, 0.8])
    with col_prog:
        st.progress(
            idx / total_q,
            text=f"Question {idx + 1} of {total_q}  ·  {cfg.get('topic','')}",
        )
    with col_score:
        if st.session_state.total_marks > 0:
            st.markdown(
                f'<div style="padding-top:.35rem;"><span class="score-pill">'
                f'{st.session_state.total_score}/{st.session_state.total_marks}</span></div>',
                unsafe_allow_html=True,
            )
    with col_streak:
        if st.session_state.streak > 1:
            st.markdown(
                f'<div style="padding-top:.45rem;" class="streak-chip">🔥 {st.session_state.streak}</div>',
                unsafe_allow_html=True,
            )

    # ── Question card ──
    type_labels = {"mcq": "MCQ", "short": "SHORT ANSWER", "structured": "STRUCTURED"}
    st.markdown(
        f"""<div class="q-card">
            <div class="q-meta">{type_labels.get(q_type,'QUESTION')} &nbsp;·&nbsp; {cfg.get('board','').split()[0]} &nbsp;·&nbsp; <span class="marks-pill">{marks} MARK{'S' if marks > 1 else ''}</span></div>
            <div class="q-text">{q['question']}</div>
        </div>""",
        unsafe_allow_html=True,
    )

    # ── Answer input (only if not yet answered) ──
    if not answered:
        if q_type == "mcq":
            opts = q.get("options", {})
            choices = [f"{k} — {v}" for k, v in opts.items()]
            selected = st.radio("Select your answer:", choices, key=f"radio_{idx}", index=None)

            btn_col, skip_col = st.columns([3, 1])
            with btn_col:
                if st.button("Submit Answer", key=f"sub_{idx}"):
                    if selected is None:
                        st.warning("Select an option first.")
                    else:
                        letter = selected.split(" — ")[0].strip()
                        correct_letter = q.get("correct_option", "")
                        correct = letter == correct_letter
                        correct_text = opts.get(correct_letter, "")

                        fb = {
                            "marks_awarded": marks if correct else 0,
                            "marks_hit":    [f"{correct_letter}: {correct_text}"] if correct else [],
                            "marks_missed": [] if correct else [f"Correct: {correct_letter} — {correct_text}"],
                            "feedback":     ("Correct! Well done." if correct
                                             else f"Incorrect. The right answer was {correct_letter}: {correct_text}."),
                            "model_answer": q.get("model_answer", ""),
                            "tip":          ("" if correct
                                             else (q.get("mark_scheme", [""])[0] if q.get("mark_scheme") else "")),
                        }
                        _record_answer(idx, selected, fb, marks)
            with skip_col:
                st.markdown('<div class="btn-ghost">', unsafe_allow_html=True)
                if st.button("Skip", key=f"skip_{idx}"):
                    _skip_question(idx, q)
                st.markdown("</div>", unsafe_allow_html=True)

        else:
            st.markdown(
                f'<p style="color:var(--accent-light);font-size:.82rem;font-weight:500;">'
                f'Aim for <strong>{marks}</strong> distinct marking points.</p>',
                unsafe_allow_html=True,
            )
            student_ans = st.text_area(
                "Your answer:", height=200, key=f"text_{idx}",
                placeholder="Write your full answer here. Be precise — vague phrasing doesn't earn marks.",
            )

            btn_col, skip_col = st.columns([3, 1])
            with btn_col:
                if st.button("Submit & Mark", key=f"sub_{idx}"):
                    if not student_ans.strip():
                        st.warning("Write an answer before submitting.")
                    else:
                        with st.spinner("Marking…"):
                            try:
                                fb = evaluate_answer(q, student_ans)
                            except Exception as e:
                                st.error(f"Marking failed: {e}")
                                st.stop()
                        _record_answer(idx, student_ans, fb, marks)
            with skip_col:
                st.markdown('<div class="btn-ghost">', unsafe_allow_html=True)
                if st.button("Skip", key=f"skip_{idx}"):
                    _skip_question(idx, q)
                st.markdown("</div>", unsafe_allow_html=True)

    # ── Feedback (shown after answering) ──
    if answered:
        fb          = st.session_state.feedback[idx]
        ma          = fb.get("marks_awarded", 0)
        pct_q       = ma / marks * 100 if marks else 0

        if pct_q == 100:
            fb_class, icon, label = "fb-correct", "✅", f"Full marks — {ma}/{marks}"
        elif pct_q >= 50:
            fb_class, icon, label = "fb-partial", "⚡", f"Partial credit — {ma}/{marks}"
        else:
            fb_class, icon, label = "fb-wrong", "✗", f"Needs work — {ma}/{marks}"

        st.markdown(
            f"""<div class="{fb_class}">
                <div style="font-size:1.1rem;font-weight:700;font-family:'Manrope',sans-serif;margin-bottom:.5rem;">{icon} {label}</div>
                <div style="font-size:.92rem;line-height:1.6;">{fb.get('feedback','')}</div>
            </div>""",
            unsafe_allow_html=True,
        )

        # Mark scheme breakdown
        with st.expander("📋 Mark Scheme Breakdown", expanded=True):
            for pt in fb.get("marks_hit", []):
                st.markdown(f'<div class="point-hit">✓ {pt}</div>', unsafe_allow_html=True)
            for pt in fb.get("marks_missed", []):
                st.markdown(f'<div class="point-miss">✗ {pt}</div>', unsafe_allow_html=True)

        # Model answer
        with st.expander("📖 Model Answer"):
            st.markdown(
                f'<div class="model-ans">{fb.get("model_answer") or q.get("model_answer","")}</div>',
                unsafe_allow_html=True,
            )

        # Tip
        if fb.get("tip"):
            st.markdown(
                f'<div class="tip-block">💡 <strong>Tip:</strong> {fb["tip"]}</div>',
                unsafe_allow_html=True,
            )

        st.markdown("<br>", unsafe_allow_html=True)

        next_label = "Next Question →" if idx < total_q - 1 else "See Results 🏁"
        if st.button(next_label, key="next_btn"):
            st.session_state.current_q += 1
            if st.session_state.current_q >= total_q:
                st.session_state.view = "results"
            st.rerun()


def _record_answer(idx: int, answer: str, fb: dict, marks: int) -> None:
    """Persist answer + feedback and update running score."""
    st.session_state.answers[idx]  = answer
    st.session_state.feedback[idx] = fb
    st.session_state.total_score  += fb.get("marks_awarded", 0)
    st.session_state.total_marks  += marks

    pct = fb.get("marks_awarded", 0) / marks * 100 if marks else 0
    if pct == 100:
        st.session_state.streak += 1
        st.session_state.max_streak = max(st.session_state.streak, st.session_state.max_streak)
    elif pct < 50:
        st.session_state.streak = 0
    st.rerun()


def _skip_question(idx: int, q: dict) -> None:
    st.session_state.answers[idx]  = "[SKIPPED]"
    st.session_state.feedback[idx] = {
        "marks_awarded": 0,
        "marks_hit":     [],
        "marks_missed":  q.get("mark_scheme", []),
        "feedback":      "Question skipped.",
        "model_answer":  q.get("model_answer", ""),
        "tip":           "",
    }
    st.session_state.total_marks += q.get("marks", 1)
    st.session_state.streak       = 0
    st.session_state.current_q   += 1
    if st.session_state.current_q >= len(st.session_state.questions):
        st.session_state.view = "results"
    st.rerun()


# ──────────────────────────────────────────────────────────────────────────────
# VIEW: RESULTS
# ──────────────────────────────────────────────────────────────────────────────
def render_results() -> None:
    total   = st.session_state.total_score
    avail   = st.session_state.total_marks
    pct     = total / avail * 100 if avail else 0
    grade   = get_grade(pct)
    g_col   = grade_color(grade)
    cfg     = st.session_state.quiz_config
    qs      = st.session_state.questions

    # ── Grade hero ──
    st.markdown(
        f"""<div style="text-align:center;padding:2rem 0 1rem;">
            <div class="grade-circle" style="background:rgba(124,106,247,.1);border:3px solid {g_col};color:{g_col};">{grade}</div>
            <div style="font-family:'Manrope',sans-serif;font-size:1.8rem;font-weight:800;color:#dfe6e9;">{total} / {avail} marks · {pct:.0f}%</div>
            <div style="color:var(--muted);font-size:.9rem;margin-top:.3rem;">{cfg.get('subject','')} · {cfg.get('topic','')} · {cfg.get('board','')}</div>
            <div style="color:var(--muted);font-size:.8rem;margin-top:.2rem;">Best streak: 🔥 {st.session_state.max_streak}</div>
        </div>""",
        unsafe_allow_html=True,
    )

    # ── Grade boundary bar ──
    st.markdown("**Grade Boundaries**")
    cols = st.columns(len(GRADE_THRESHOLDS))
    for col, (g, threshold) in zip(cols, GRADE_THRESHOLDS):
        with col:
            is_you   = g == grade
            bg       = grade_color(g) if is_you else "var(--card)"
            fg       = "#0d0e17" if is_you and g == "A*" else ("#dfe6e9" if is_you else "var(--muted)")
            border   = grade_color(g) if is_you else "var(--border)"
            weight   = "800" if is_you else "400"
            st.markdown(
                f"""<div class="boundary-item" style="background:{bg};border:1px solid {border};color:{fg};font-weight:{weight};">
                    {g}<div style="font-size:.65rem;font-weight:400;opacity:.75;">{threshold}%+</div>
                </div>""",
                unsafe_allow_html=True,
            )

    st.divider()

    # ── Per-question review ──
    st.markdown("### Question Review")
    for i, q in enumerate(qs):
        fb     = st.session_state.feedback.get(i, {})
        ma     = fb.get("marks_awarded", 0)
        mt     = q.get("marks", 1)
        q_pct  = ma / mt * 100 if mt else 0
        icon   = "✅" if q_pct == 100 else ("⚡" if q_pct >= 50 else "✗")
        short  = q["question"][:85] + ("…" if len(q["question"]) > 85 else "")

        with st.expander(f"{icon}  Q{i+1}: {short}  ({ma}/{mt} marks)"):
            ans = st.session_state.answers.get(i, "")
            if ans and ans != "[SKIPPED]":
                st.markdown(f"**Your answer:** {ans}")
            elif ans == "[SKIPPED]":
                st.markdown("*Question was skipped.*")
            st.markdown(f"**Feedback:** {fb.get('feedback','–')}")
            if fb.get("model_answer") or q.get("model_answer"):
                st.markdown(
                    f'<div class="model-ans">{fb.get("model_answer") or q.get("model_answer","")}</div>',
                    unsafe_allow_html=True,
                )

    st.divider()

    # ── Actions ──
    ca, cb = st.columns(2)
    with ca:
        if st.button("↺  Same Topic, New Questions"):
            _do_generate(
                cfg.get("subject",""), cfg.get("topic",""), cfg.get("board",""),
                cfg.get("diff",""), cfg.get("q_type_label",""), cfg.get("num_q",5),
            )
    with cb:
        st.markdown('<div class="btn-ghost">', unsafe_allow_html=True)
        if st.button("📚  Choose New Topic"):
            _reset()
        st.markdown("</div>", unsafe_allow_html=True)


# ──────────────────────────────────────────────────────────────────────────────
# MAIN
# ──────────────────────────────────────────────────────────────────────────────
def main() -> None:
    init_state()
    st.markdown(CSS, unsafe_allow_html=True)
    render_sidebar()

    view = st.session_state.get("view", "home")

    if not st.session_state.get("questions"):
        render_home()
    elif view == "quiz":
        render_quiz()
    elif view == "results":
        render_results()
    else:
        render_home()


if __name__ == "__main__":
    main()
