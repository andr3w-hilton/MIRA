# MIRA — Future Improvements

Ideas for making Mira's learning more emergent and less "Claude wearing a mask."

---

## 1. Memory That Shapes Behavior

- [ ] **Weighted interests** — Track topics with engagement scores so topic selection is pulled toward natural clusters, rather than Claude picking arbitrarily
- [ ] **Contradiction log** — Detect when today's reflection conflicts with a previous one and force Mira to reconcile
- [x] **Forgetting / memory decay** — Older memories compress or fade, forcing Mira to rebuild understanding rather than parrot saved text

## 2. Environment That Pushes Back

- [ ] **Code execution** — Let Mira write and run code related to what she's learning; test results are real feedback Claude can't hallucinate
- [ ] **Predictions before research** — Before researching a topic, write down expectations; after research, compare prediction vs reality
- [ ] **Quizzes on past material** — Periodically test Mira on old topics without access to memory files to see what she actually "knows"

## 3. Reduce Claude's Role to Evaluator, Not Author

- [ ] **Topic selection from candidates** — Generate multiple topic proposals from different heuristics (trending articles, random walks, knowledge gaps); Claude picks from a menu instead of inventing
- [ ] **Evolving reflection templates** — Use a structured reflection format that Mira modifies over time; the structure itself becomes a learned artifact
- [ ] **Separate learner from critic** — Two Claude calls with different system prompts (one generates, one evaluates); tension between them creates something neither would alone

## 4. Make the Growth Mechanism Actually Matter

- [ ] **Plugin-based core loop** — Daily cycle discovers and loads modules from a `skills/` directory
- [ ] **Merged skills actually run** — A proposed-and-merged skill runs in the next cycle, genuinely altering behavior
- [ ] **Self-modifiable prompts** — Let Mira propose changes to her own reflection prompts, research strategies, or memory structures

## 5. Multi-Source Learning With Disagreement

- [x] **Multiple research sources** — Topic decomposition added: Mira breaks abstract questions into 2-3 concrete Wikipedia search terms and combines results. Staying Wikipedia-only for now by design.
- [ ] **Source disagreement handling** — When sources conflict, force Mira to reason about why and pick a position
- [ ] **Position tracking over time** — Record how her views evolve as she encounters new information

## 6. Social Learning

- [x] **Andrew's notes** — `memory/notes_from_andrew.md` — edit on GitHub, Mira reads at wake-up, factors into topic choice and reflection. Clear after she responds.
- [ ] **Substantive questions to Andrew** — Ask real questions (not just boundary checks) whose answers feed into future learning
- [ ] **Multi-instance discussion** — Multiple Mira instances with different identities "discuss" topics by reading each other's reflections

---

## Pending

- [ ] **Closing the proposal loop** — Code proposals (`proposals/*.py`) are merged but never run. Need a pathway from "approved proposal" to "active feature". Options: (1) manual integration by Andrew — review and move into `brain/`; (2) plugin-based loader — cycle auto-imports from a `skills/` dir; (3) sandboxed trial run on merge before touching the main cycle. Identity proposals already work end-to-end. Code proposals are a graveyard. Fix this next.
- [x] **Frontend** — Built and live at https://andr3w-hilton.github.io/MIRA/. Auto-publishes on each cycle via GitHub Actions. Cream/coral HER aesthetic, animated Omicron Ceti waveform, memory tier bars, tomorrow's question. Mobile responsive.
- [x] **Telegram bot** — Reviewed. No changes needed. Mira uses her own `notify.py` (simple HTTP sendMessage). The AI_Tools scheduler bot is a separate tool and doesn't conflict.
