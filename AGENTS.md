# Engineering Guidelines — API Sentinel

## Standards & Expectations
All agent interactions and contributions to this repository must follow the principles in [.gemini/rules/unbiased-review.md](.gemini/rules/unbiased-review.md):

- **No sycophancy or empty praise**: Provide objective, evidence-based technical critique ([.gemini/rules/unbiased-review.md](.gemini/rules/unbiased-review.md)).
- **Ponytail Minimalist Engineering**: Follow YAGNI, reject premature abstraction, and prioritize standard libraries over dependency bloat ([.gemini/rules/ponytail.md](.gemini/rules/ponytail.md)).
- **Security & Integrity First**: Strictly enforce typing, input validation (Pydantic), schema migrations (Alembic), and secure credential handling.
- **Adversarial Review**: Proactively inspect diffs for edge-case failures, unhandled exceptions, and scalability bottlenecks.

