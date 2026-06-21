# Comparison: Regular Search vs. AI Bot Search

This document explains the key differences between the two search endpoints.

---

## The Main Difference at a Glance

| Feature | `POST /search` (Regular Search) | `POST /search/bot` (AI Bot Search) |
| :--- | :--- | :--- |
| **Technology** | Static Python Code (Regex & Whitelists) | Generative Artificial Intelligence (Groq LLM) |
| **How it Works** | Scans the query for exact letters and numbers. | Understands the context and meaning of the sentence. |
| **Speed / Cost** | Instant, free to run. | Sub-second, requires a lightweight API call. |
| **Flexibility** | Rigid (cannot understand synonyms). | High (handles typos, synonyms, and ranges). |

---

## How They Handle the Same Query: An Example

Imagine a recruiter searches for: 
> *"I want a backend coder with 3 to 5 years of experience"*

### 1. Regular Search (`/search`)
*   **What it does:** Runs basic code matching in [parse_query()](file:///c:/Users/hasna/Downloads/project%20phase%201/project%20phase%201/project%20phase%201/main.py#L273).
*   **The Problem:** 
    *   It doesn't find the word "python" or "django" in its whitelist, so it thinks **0 skills** are requested.
    *   It looks for a number followed by the word "year" and only grabs the first number (`3`). It has no idea what `5` represents.
*   **Result:** It searches for someone with `3 years` of experience but doesn't look for any backend skills.

### 2. AI Bot Search (`/search/bot`)
*   **What it does:** Sends the query to the AI in [ai_parse_query()](file:///c:/Users/hasna/Downloads/project%20phase%201/project%20phase%201/project%20phase%201/main.py#L283).
*   **The Solution:**
    *   The AI understands that *"backend coder"* means technical skills like Python or Node, and classifies "backend" as a keyword filter.
    *   It understands the range: **Minimum Experience:** 3 years, **Maximum Experience:** 5 years.
*   **Result:** It returns a highly accurate list of candidates who are mid-level backend developers, ranking them precisely.
