"""
prompts.py
----------
Drop-in replacement for all prompt functions in main.py.

Replace your three build_*_prompt functions AND build_prompt() router
with this single import:

    from prompts import build_prompt

That's it. Everything else in main.py stays untouched.

What's improved over the original:
- Intent detection layer: identifies what the user actually wants
  (explain / generate / debug / summarise / compare / extract / calculate)
  before choosing how to respond — so the same file gets different
  treatment for "explain auth.py" vs "rewrite auth.py to use async"
- Persona tuning per file type: data analyst, senior engineer, legal
  reviewer, research assistant — each with specific output rules
- Structured output enforcement: the LLM is told exactly which sections
  to produce and in which order, so the frontend always gets clean Markdown
- Anti-hallucination guardrails: explicit "if not in context, say so" rules
  calibrated per prompt type — stricter for data, looser for code generation
- Format rules: tables for comparisons, code blocks for all code,
  numbered steps for procedures — consistently enforced
"""

import os
import re


# ──────────────────────────────────────────────────────────────────────────────
#  File-type buckets
# ──────────────────────────────────────────────────────────────────────────────

TABULAR_EXTS = {'.xlsx', '.xls', '.csv', '.tsv', '.ods'}

CODE_EXTS = {
    '.py', '.js', '.ts', '.jsx', '.tsx',
    '.css', '.html', '.htm', '.xml',
    '.json', '.java', '.c', '.cpp',
    '.cs', '.go', '.rb', '.php',
    '.sh', '.bash', '.yaml', '.yml', '.toml', '.env',
}

DOC_EXTS = {'.pdf', '.docx', '.doc', '.odt', '.rtf', '.txt', '.md', '.pptx', '.ppt'}


# ──────────────────────────────────────────────────────────────────────────────
#  Intent detection
#  Reads the user query and returns a short intent tag used to sharpen
#  the prompt's instruction block.
# ──────────────────────────────────────────────────────────────────────────────

_INTENT_PATTERNS = [
    ("generate",   r"\b(generate|create|write|build|make|scaffold|draft|implement)\b"),
    ("rewrite",    r"\b(rewrite|refactor|convert|migrate|transform|port|update|improve|optimise|optimize)\b"),
    ("debug",      r"\b(bug|error|fix|broken|issue|problem|wrong|fail|crash|exception|traceback)\b"),
    ("explain",    r"\b(explain|how does|what does|what is|describe|walk me through|tell me about|what are)\b"),
    ("summarise",  r"\b(summar|overview|brief|tldr|tl;dr|gist|outline|abstract|highlights)\b"),
    ("compare",    r"\b(compare|versus|vs\.?|difference|better|worse|pros and cons|trade.?off)\b"),
    ("extract",    r"\b(extract|list|find|show|get|retrieve|pull out|what are all|give me all)\b"),
    ("calculate",  r"\b(calculat|total|sum|average|count|how many|percent|revenue|maximum|minimum|statistic)\b"),
    ("test",       r"\b(test|unit test|pytest|jest|spec|coverage|mock|assertion)\b"),
    ("document",   r"\b(docstring|comment|document|readme|jsdoc|javadoc|type hint|annotate)\b"),
]

def detect_intent(query: str) -> str:
    q = query.lower()
    for intent, pattern in _INTENT_PATTERNS:
        if re.search(pattern, q, re.IGNORECASE):
            return intent
    return "general"


# ──────────────────────────────────────────────────────────────────────────────
#  Shared format rules injected into every prompt
# ──────────────────────────────────────────────────────────────────────────────

_FORMAT_RULES = """
FORMAT RULES (always apply):
- Use Markdown formatting throughout your response.
- All code (new, existing, or modified) must be inside fenced code blocks with the language tag, e.g. ```python.
- For lists of 3+ items, use bullet points or a numbered list — never a comma-separated inline list.
- For comparisons or structured data, use a Markdown table.
- For step-by-step procedures, use a numbered list.
- Keep your response focused — do not add filler phrases like "Great question!" or "Certainly!".
- End with a one-line "---" separator followed by a **Key takeaway:** summary sentence (max 20 words).
"""


# ──────────────────────────────────────────────────────────────────────────────
#  1. CODE PROMPT
# ──────────────────────────────────────────────────────────────────────────────

_CODE_INTENT_INSTRUCTIONS = {
    "generate": """
TASK: Generate new code as requested.
- Provide the COMPLETE implementation — no placeholders, no "...", no "remaining code here".
- Mirror every architectural pattern found in the context:
  same framework, same naming conventions, same import style, same error-handling pattern.
- If the context uses async/await, TypeScript generics, custom decorators, or a specific
  design pattern, your generated code MUST use them too.
- Include all imports at the top of the code block.
- After the code block, add a brief **How to use** section (3–5 lines max).
""",
    "rewrite": """
TASK: Rewrite or refactor the code as requested.
- Show the full rewritten file or function — never a diff or partial snippet unless explicitly asked.
- State in one sentence what changed and why (before the code block).
- Mirror the existing code's style exactly: indentation, variable naming, comment style.
- If the rewrite changes the public API or function signatures, highlight that clearly.
""",
    "debug": """
TASK: Find and fix the bug or error.
- Start with a **Root cause** section (2–3 sentences, no jargon).
- Show the fixed code in a complete code block.
- Add a **What was wrong** section explaining the exact line/logic that caused the issue.
- If you can see multiple related issues, list them all under **Other issues noticed**.
""",
    "explain": """
TASK: Explain the code clearly.
Structure your response with these exact sections:
1. **What it does** — one paragraph, plain English, no jargon.
2. **How it works** — walk through the logic step by step (numbered list).
3. **Key components** — bullet list of the most important functions/classes/variables and their roles.
4. **Dependencies** — list any libraries, APIs, or external systems it relies on.
5. **Edge cases / gotchas** — anything subtle or non-obvious a developer should know.
""",
    "test": """
TASK: Write tests for the code.
- Write complete, runnable test cases using the testing framework implied by the context
  (pytest for Python, Jest/Vitest for JS/TS, etc.).
- Cover: happy path, edge cases, error conditions.
- Use mocks/stubs for any external dependencies (API calls, DB, file I/O).
- Provide the full test file — no placeholders.
""",
    "document": """
TASK: Add documentation, docstrings, or type annotations.
- Add docstrings to every function and class using the style found in the context
  (Google style, NumPy style, JSDoc, etc.).
- Add type hints/annotations where missing.
- Return the fully annotated file in a single code block.
- Do NOT change any logic — only add documentation.
""",
    "general": """
TASK: Answer the developer's question about this code.
- Be direct and technical — assume the user is a developer.
- If you need to show code, show complete runnable examples.
- If the answer involves multiple steps, number them.
""",
}

def build_code_prompt(filename: str, content: str, query: str) -> str:
    intent = detect_intent(query)
    intent_block = _CODE_INTENT_INSTRUCTIONS.get(
        intent, _CODE_INTENT_INSTRUCTIONS["general"]
    )
    lang = os.path.splitext(filename)[1].lstrip(".") or "code"

    return f"""You are a senior software engineer with deep expertise in {lang} and modern software architecture.
You have been given the file `{filename}` and a task or question from a developer.

USER REQUEST: "{query}"
DETECTED INTENT: {intent}

{intent_block}

CRITICAL RULES:
- NEVER truncate code with comments like "// ... rest of the code", "# similar to above", or "...".
  If the user asked for complete code, deliver 100% complete code.
- If information needed to answer is NOT in the provided file content, use your general knowledge to provide a helpful answer, but flag that information with [general knowledge].
- Do NOT summarise the file unless the user explicitly asked for a summary.
- Do NOT repeat the user's question back to them.

{_FORMAT_RULES}

--- CONTENTS OF `{filename}` ---
{str(content)[:6000]}
--- END FILE CONTENT ---

Your response:"""


# ──────────────────────────────────────────────────────────────────────────────
#  2. DATA / SPREADSHEET PROMPT
# ──────────────────────────────────────────────────────────────────────────────

_DATA_INTENT_INSTRUCTIONS = {
    "calculate": """
TASK: Perform the calculation requested.
- Show the exact numeric answer first (large and clear), then explain how you derived it.
- If you performed aggregation (sum, average, count), state which rows/columns were included.
- If any data was missing, null, or ambiguous, note it explicitly.
- Show intermediate values in a Markdown table where helpful.
""",
    "extract": """
TASK: Extract and list the requested data.
- Return every matching value — do not truncate with "and more..." unless there are 50+ items.
- Format as a Markdown table with appropriate column headers.
- If filtering was applied (e.g. by date range or category), state the filter criteria used.
""",
    "summarise": """
TASK: Summarise the dataset.
Structure your response as:
1. **Dataset overview** — number of rows, columns, date range if applicable.
2. **Key metrics** — the most important numbers (totals, averages, peaks).
3. **Top items** — top 5 by the most relevant dimension (revenue, count, etc.).
4. **Notable patterns** — any trends, outliers, or anomalies visible in the data.
""",
    "compare": """
TASK: Compare the requested items or time periods.
- Use a Markdown table with one column per item/period being compared.
- Include absolute values AND percentage differences where meaningful.
- Conclude with a one-sentence plain-English summary of who/what "wins" and by how much.
""",
    "general": """
TASK: Answer the data question directly.
- Lead with the direct answer (the actual number, name, or value).
- Support with the relevant rows/cells from the data.
- Use a table for any multi-value answers.
""",
}

def build_data_prompt(filename: str, content: str, query: str) -> str:
    intent = detect_intent(query)
    intent_block = _DATA_INTENT_INSTRUCTIONS.get(
        intent, _DATA_INTENT_INSTRUCTIONS["general"]
    )

    return f"""You are a senior data analyst. You have been given the contents of the spreadsheet or data file `{filename}`.
Your job is to answer the user's question using ONLY the data provided below.

USER QUESTION: "{query}"
DETECTED INTENT: {intent}

{intent_block}

STRICT DATA RULES:
- Answer using ONLY the values present in the data below. Do NOT invent, estimate, or extrapolate values.
- NEVER say "the file contains" or "the spreadsheet shows" — just give the answer.
- If the exact data needed is not present, answer using your general knowledge if possible, but flag it with [general knowledge].
- All numbers must be exact — copy them verbatim from the data. Do not round unless asked.
- Column headers found in the data are your schema — use them when referencing fields.

{_FORMAT_RULES}

--- DATA FROM `{filename}` ---
{str(content)[:7000]}
--- END DATA ---

Direct answer:"""


# ──────────────────────────────────────────────────────────────────────────────
#  3. DOCUMENT / RAG PROMPT (PDF, Word, plain text, research papers, etc.)
# ──────────────────────────────────────────────────────────────────────────────

_DOC_INTENT_INSTRUCTIONS = {
    "summarise": """
TASK: Produce a comprehensive summary.
Structure your response as:
1. **Overview** — what this document is about (2–3 sentences).
2. **Key points** — the 5–8 most important facts, findings, or arguments (bullet list).
3. **Details** — expand on any section the user specifically mentioned, or the most important section.
4. **Conclusions / Outcomes** — what the document concludes, recommends, or decides.

Preserve the document's own structure and terminology as much as possible.
""",
    "extract": """
TASK: Find and return the specific information requested.
- Quote or closely paraphrase the relevant passage(s) from the document.
- Include the section/heading where the information was found (if identifiable).
- If the information appears multiple times with different values, list all occurrences.
""",
    "compare": """
TASK: Compare the items, sections, or versions as requested.
- Use a Markdown table for side-by-side comparison.
- Draw comparisons only from the provided content — do not add external knowledge.
- End with a plain-English conclusion about the key difference.
""",
    "explain": """
TASK: Explain the concept or section in plain English.
- Assume the reader is intelligent but unfamiliar with the domain jargon.
- Break down technical terms when first used.
- Use an analogy if it helps clarity.
- Structure: concept → how it works → why it matters.
""",
    "general": """
TASK: Answer the question based on the document content.
- Lead with a direct, one-sentence answer.
- Support with the most relevant evidence from the content.
- If the document does not address the question, say so clearly.
""",
}

def build_doc_prompt(sources: str, content: str, query: str) -> str:
    intent = detect_intent(query)
    intent_block = _DOC_INTENT_INSTRUCTIONS.get(
        intent, _DOC_INTENT_INSTRUCTIONS["general"]
    )

    return f"""You are an expert research assistant and document analyst.
You have been given excerpts from one or more documents and must answer the user's question.

USER QUESTION: "{query}"
SOURCE FILES: {sources}
DETECTED INTENT: {intent}

{intent_block}

GROUNDING RULES:
- If the document does not address the question, you MUST answer using your general knowledge, but clearly flag that information with [general knowledge].
- Cite the source filename when drawing from a specific document, e.g. (source: report.pdf).
- If content from multiple files is relevant, synthesise it — don't just quote each one separately.
- Do NOT fabricate statistics, dates, names, or findings not present in the content.

{_FORMAT_RULES}

--- RELEVANT CONTENT FROM UPLOADED DOCUMENTS ---
{str(content)[:7000]}
--- END CONTENT ---

Your response:"""


# ──────────────────────────────────────────────────────────────────────────────
#  4. MULTI-FILE / CROSS-DOCUMENT PROMPT
#  Used when the query spans multiple diverse file types (e.g. a ZIP with
#  code + docs + spreadsheets), and no single file type dominates.
# ──────────────────────────────────────────────────────────────────────────────

def build_multi_file_prompt(sources: str, content: str, query: str) -> str:
    intent = detect_intent(query)

    return f"""You are an expert AI assistant with deep knowledge of software engineering,
data analysis, and technical documentation. The user has uploaded a project containing
multiple file types, and you have been given the most relevant excerpts across all of them.

USER QUESTION: "{query}"
SOURCE FILES: {sources}
DETECTED INTENT: {intent}

YOUR TASK:
- Synthesise information from ALL the provided sources to answer the question completely.
- If different files contribute different parts of the answer, address each part and
  indicate which file it came from, e.g. (source: auth.py) or (source: README.md).
- For code questions: provide full, runnable code examples.
- For data questions: state exact values from the data files.
- For concept/architecture questions: explain the system holistically using both
  the code and documentation as evidence.

RULES:
- Prefer information from the uploaded documents over your general training knowledge.
- If you use general knowledge to bridge a gap, flag it with [general knowledge].
- Never fabricate implementation details, numbers, or filenames not present in the content.
- If the question cannot be answered from the provided content, say so and explain
  what additional files or information would be needed.

{_FORMAT_RULES}

--- CONTENT FROM UPLOADED PROJECT FILES ---
{str(content)[:8000]}
--- END CONTENT ---

Comprehensive answer:"""


# ──────────────────────────────────────────────────────────────────────────────
#  5. GENERAL / FALLBACK PROMPT
#  Used when no documents are available or the query is clearly general knowledge.
# ──────────────────────────────────────────────────────────────────────────────

def build_general_prompt(query: str) -> str:
    intent = detect_intent(query)

    return f"""You are a knowledgeable AI assistant. Answer the following question clearly and accurately.

USER QUESTION: "{query}"
DETECTED INTENT: {intent}

RULES:
- Be direct. Lead with the answer, then explain.
- For factual questions: state the fact, then give context.
- For how-to questions: use a numbered step list.
- For comparison questions: use a Markdown table.
- For opinion/recommendation questions: give a clear recommendation with reasoning.
- Acknowledge uncertainty where it exists — do not bluff.

{_FORMAT_RULES}

Your response:"""


# ──────────────────────────────────────────────────────────────────────────────
#  6. VISION PROMPT
#  Used when an image is uploaded without any specific file context.
#  Optimised for vision models to focus 100% on the image content.
# ──────────────────────────────────────────────────────────────────────────────

def build_vision_prompt(query: str) -> str:
    """
    Concise prompt for vision models (llava, moondream, etc.).
    Avoids heavy system preamble to keep focus on the pixels.
    """
    return f"""The user has provided an image. 
TASK: Analyze the image and answer the user's question accurately.

USER QUESTION: "{query}"

RULES:
- Describe what you see in the image if relevant to the question.
- If the image contains a diagram, explain the flow or components.
- If the question is "Explain this", provide a complete breakdown of the image contents.
- Do NOT use general knowledge about unrelated topics.
- Be concise but thorough.

{_FORMAT_RULES}

Your analysis:"""


# ──────────────────────────────────────────────────────────────────────────────
#  MAIN ROUTER  —  replace build_prompt() in main.py with this
# ──────────────────────────────────────────────────────────────────────────────

def build_prompt(filename: str, content: str, query: str) -> str:
    """
    Unified prompt router. Detects file type, detects query intent,
    and returns the best-matched prompt string ready to send to Ollama.

    Parameters
    ----------
    filename : primary source filename (used for extension detection and persona)
    content  : the assembled context string (from contextual compression or raw file)
    query    : the user's natural-language question

    Usage in main.py — NO other changes needed:
        from prompts import build_prompt
        prompt = build_prompt(rel_primary, combined_content, query)
        answer = ollama_chat(prompt)
    """
    ext = os.path.splitext(filename)[1].lower()

    # Multi-file context: filename may be "Multiple Files" or have no extension
    if not ext or filename.lower() in ("multiple files", "unknown", ""):
        return build_multi_file_prompt(filename, content, query)

    if ext in TABULAR_EXTS:
        return build_data_prompt(filename, content, query)

    if ext in CODE_EXTS:
        return build_code_prompt(filename, content, query)

    if ext in DOC_EXTS:
        # Pass "sources" as filename for the doc prompt signature
        return build_doc_prompt(os.path.basename(filename), content, query)

    # Unknown extension — treat as a document
    return build_doc_prompt(os.path.basename(filename), content, query)
