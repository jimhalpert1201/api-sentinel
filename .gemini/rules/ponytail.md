# Ponytail Philosophy: The Minimalist Senior Engineer

## Core Axiom
> **"The best code is the code you never wrote."**

Ponytail counters the LLM tendency to over-engineer, hallucinate boilerplate, and bloat codebases with unnecessary abstractions and heavy third-party packages.

---

## The Decision Ladder (Enforce Before Writing Any Code)

Before writing any new function, class, or abstraction, you must evaluate this ladder from top to bottom:

1. **Do Nothing (YAGNI)**: Can this problem be solved without new code? If the requirement is speculative or a "future nice-to-have", reject it.
2. **Native Language / Standard Library**: Does Python's standard library (or TypeScript's native APIs) already solve this? (e.g., `dataclasses`, `enum`, `pathlib`, `itertools`, `httpx`). Do not add external packages if standard tools suffice.
3. **Existing Code**: Can an existing function, query, or utility handle this with a minor parameter adjustment? Never duplicate logic.
4. **Single Small Function**: If new code must be written, write the smallest possible standalone function. No premature classes, factories, or deep inheritance trees.
5. **Full Abstraction (Last Resort)**: Only create custom classes, design patterns, or new layers if there are at least three distinct, proven call sites requiring polymorphism.

---

## Anti-Bloat Guardrails
* **No Premature Architecture**: Do not create service layers, repositories, and interfaces for simple 5-line operations.
* **Keep Dependencies Minimal**: Every new dependency in `requirements.txt` or `package.json` must be strictly justified.
* **Trim Dead Code**: If code is no longer called, delete it immediately. Do not comment it out.
* **Short, Readable Diffs**: Favor clarity and conciseness over clever or verbose code.
