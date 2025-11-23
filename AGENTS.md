# AGENTS

This project has a single “agent” component used during PDF-to-Markdown conversion when the user opts in to OpenAI-assisted OCR/math extraction.

## PDF Conversion AI Agent
- **Location:** `converter/ai_agent.py`
- **Used by:** `converter/engine.PDFConverter.convert` (spawned from `gui/mainwindow.ConversionWorker` when the UI toggle “Use AI Agent (OpenAI)” is enabled and an API key is present).
- **Role:** Transcribes a PDF page image into Markdown, cleaning headers/footers, formatting math, and optionally emitting YAML frontmatter on the first page.
- **Invocation flow:**  
  1) UI collects files → `ConversionWorker` (QThread) → `PDFConverter.convert`.  
  2) For each page, the converter renders it to a 2× PNG, base64-encodes it, and calls `AIAgent.convert_page`.  
  3) The agent sends a single `chat.completions` request with the image payload and a structured prompt that: strips repeated headers/footers, uses `$`/`$$` for LaTeX, describes images instead of embedding them, and adds YAML metadata only on page 1.  
  4) The Markdown from the response is appended to the output file (`<pdf>.md` by default). Progress is reported to the UI.
- **Inputs:** API key, model (`gpt-4o`, `gpt-4o-mini`, `gpt-3.5-turbo`), page PNG bytes, page index (for metadata logic). Optional `ai_model` is set via Settings.
- **Outputs:** Raw Markdown string per page. On failure, returns an HTML comment with the error text to avoid crashing the batch.
- **Config & storage:** API key and model are persisted in `QSettings` under the app namespace (`MyCompany/PDFtoMD`). No other state is stored.
- **Error handling:** Exceptions inside the agent are caught and returned as comments; thread-level errors surface via `ConversionWorker.error` to the UI. Local fallback conversion (pymupdf4llm) is used when the AI toggle is off or no key is provided.
- **Privacy/security notes:** Entire page images are sent to OpenAI; do not enable AI mode for sensitive documents. The prompt forbids image embedding and code blocks but does not perform redaction.
- **Performance/limits:** Each page is a single request (max_tokens=4096). Large or image-heavy pages will be slower due to the 2× render and upload size. No built-in rate limiting beyond OpenAI defaults.
- **Testing:** Network calls are not exercised in the current test suite; behavior is mostly covered manually. The rest of the converter pipeline has regression tests around exports and unit handling.

## Extending agents
- Add new providers or prompts by implementing a sibling to `AIAgent` and branching inside `PDFConverter.convert`.
- Keep prompts concise; prefer deterministic formatting rules (math delimiters, YAML placement, image description).
- If adding retries, rate limits, or batching, ensure the UI progress callback still advances per page and surfaces failures without blocking the rest of the queue.
