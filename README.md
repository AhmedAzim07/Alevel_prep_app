# A-Level StudyBot

AI-powered exam prep for Cambridge, Edexcel, AQA, and OCR. Generates real exam-style questions, marks your answers against actual mark scheme criteria, and tracks your grade in real time.

Built by a student, for students.

---

## Origin

I built the first version of this during my A-levels because I couldn't find a tool that actually replicated exam conditions — most study apps just quiz you on definitions. What I needed was something that would generate a structured 6-mark "explain" question, mark my answer point-by-point like an examiner would, and tell me exactly which mark scheme points I missed. So I built it myself.

After getting into university, I rebuilt it properly — better questions, real AI marking, support for all the major exam boards, and a UI that doesn't look like a data entry form.

---

## Features

**Question generation**
- 8 subjects: Biology, Chemistry, Physics, Mathematics, Economics, Computer Science, History, Psychology
- 100+ pre-loaded curriculum topics per subject
- 4 exam boards: CAIE, Edexcel, AQA, OCR — each with board-accurate command words and style
- 4 difficulty levels: Foundation (E-D), Intermediate (C-B), Advanced (A), Exam Standard (A*)
- 3 question types: MCQ, Short Answer (2-4 marks), Structured (5-9 marks) — or Mixed

**Marking**
- MCQ: instant auto-grading
- Short/Structured: AI marks your answer against the generated mark scheme, point by point
- Shows which mark scheme points you hit and missed
- Full model answer for every question
- Specific, actionable improvement tip per question

**Progress tracking**
- Live running score and letter grade in the sidebar (updates after every question)
- Grade boundary reference bar on results screen
- Streak counter
- Full question-by-question review at the end

---

## Stack

- **Frontend**: Streamlit with custom CSS (Manrope + Inter + JetBrains Mono)
- **AI**: Google Gemini 2.5 Flash (via `google-generativeai`)
- **Hosting**: Streamlit Community Cloud

---

## Setup

### Prerequisites

- Python 3.10+
- A Google Gemini API key — get one free at [aistudio.google.com](https://aistudio.google.com). No credit card required.

### Local

```bash
git clone https://github.com/yourusername/alevel-studybot
cd alevel-studybot

pip install -r requirements.txt

# Add your API key
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
# Open secrets.toml and replace the placeholder with your actual key

streamlit run app.py
```

### Deploy (free)

1. Push this repo to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io) → New app
3. Select your repo and set the main file to `app.py`
4. Open **Advanced settings → Secrets** and paste:
   ```toml
   GEMINI_API_KEY = "your-key-here"
   ```
5. Deploy

You'll get a live URL at `yourname-studybot.streamlit.app` in about 2 minutes.

---

## Project structure

```
alevel-studybot/
├── app.py                          # Everything — UI, API calls, state management
├── requirements.txt
├── .streamlit/
│   ├── config.toml                 # Theme (dark mode, accent colour)
│   └── secrets.toml.example        # API key template
└── .gitignore
```

The whole app is a single `app.py` file. Here's where things live if you want to extend it:

| What to change | Where |
|---|---|
| Add a subject or topic | `SUBJECTS` dict at the top |
| Tweak exam board style/prompting | `EXAM_BOARDS` dict |
| Change difficulty descriptions | `DIFFICULTIES` dict |
| Edit the question generation prompt | `generate_questions()` |
| Edit the marking prompt | `evaluate_answer()` |
| Change grade thresholds | `GRADE_THRESHOLDS` list |
| Switch AI model | `generate_questions()` and `evaluate_answer()` — edit the `model=` argument |
| All styling | `CSS` string constant |

---

## API usage and cost

The Gemini API free tier (as of 2025) gives you:
- 15 requests per minute
- 1,500 requests per day
- 1 million tokens per day

For this app: a typical 5-question session with short/structured questions uses roughly 8-12 API calls (1 for generation + 1 per non-MCQ answer). At the free rate limits, you can comfortably run dozens of sessions per day before hitting anything.

If you're running this for a group of people and hitting limits, Gemini 2.5 Flash is extremely cheap on the paid tier — well under $1 for heavy daily use.

---

## Limitations

- **Accuracy**: Questions are AI-generated and not pulled from actual past papers. They're high quality and board-accurate in style, but treat them as practice material, not official content.
- **Marking**: AI marking is good but not perfect, especially on edge cases in structured answers. Use it as a guide, not a definitive grade.
- **No persistence**: Sessions don't save between refreshes. This is a Streamlit limitation.

---

## Roadmap

- [ ] RAG pipeline: ingest official syllabi PDFs so questions are anchored to the exact spec
- [ ] Timed exam mode (countdown timer, no peeking at model answers mid-session)
- [ ] Session history and weak topic tracking across sessions
- [ ] Flashcard mode for rapid topic revision
- [ ] User accounts and long-term progress tracking
- [ ] Mobile-optimised UI (requires moving off Streamlit)

---

## Contributing

Open to PRs, especially for:
- Adding more topics to existing subjects
- Fixing subject-specific inaccuracies in generated questions
- UI improvements within Streamlit's constraints

For larger changes (auth, persistence, new architecture), open an issue first to discuss.

---

If this helped you revise, a star on the repo is appreciated.
