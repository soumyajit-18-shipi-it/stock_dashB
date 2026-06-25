# Ethical AI

## Financial Disclaimer

Stock Intelligence Dashboard is an educational and analytical tool. It does not provide personalized financial advice.

## Transparency

Model types, data sources, limitations, and LLM providers are documented in:

- `docs/model-card.md`
- `docs/ai-transparency.md`
- `docs/model-limitations.md`
- `docs/model-evaluation.md`

## Language Inclusion

The app supports multilingual UI for English, Hindi, Odia, German, and French. The Indic dataset currently covers English, Hindi, and Odia finance queries. Other Indic languages require data collection and review before support claims are expanded.

## Privacy

Prompts may be sent to external LLM providers unless local Ollama is used. User-contributed dataset rows require consent and anonymization.

## Known Ethical Risks

- Users may over-trust predictive outputs.
- LLMs may produce confident but incorrect analysis.
- Small language datasets may underperform for dialectal or code-mixed users.
- Demo RLS policies are too permissive for production user data.
