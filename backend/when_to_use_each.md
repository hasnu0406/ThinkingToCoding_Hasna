# Sourcing Guide: When to Use Regular Search vs. AI Bot Search

This guide helps recruiters understand which search tool to use under different circumstances.

---

## 1. Regular Search (Without Bot)

### Best Circumstances to Use It:
*   **Searching by Name:** Finding a specific person (e.g., *"Aparna"*). It performs a direct database lookup and is 100% accurate.
*   **Exact Single-Skill Filter:** When you only want to see people who have one exact word on their profile (e.g., *"Python"*).
*   **Internet / API Outages:** If the internet goes down or the AI cloud service (Groq) is experiencing an outage, the regular search keeps working.
*   **Instant UI Suggestions:** If the frontend needs to show search suggestions *as you type* (requiring speed under 5 milliseconds).

### When It Fails / Underperforms:
*   **Conversational Phrases:** Typing *"I need a coder who knows how to use django"* will fail to find anything because the exact sentence isn't written in candidate profiles.
*   **Synonyms:** Searching for *"Programmer"* won't return candidates who wrote *"Software Developer"* or *"Engineer"* on their resume.
*   **Experience Ranges:** Searching for *"3 to 5 years"* will only match the number 3, ignoring the upper limit.

---

## 2. AI Bot Search

### Best Circumstances to Use It:
*   **Conversational Sourcing:** Typing search phrases naturally (e.g., *"Find me a mid-level developer who has deployed docker apps on AWS"*).
*   **Synonym & Context Sourcing:** Searching for *"Machine learning expert"* will find candidates with `"tensorflow"`, `"pytorch"`, or `"deep learning"` on their profile, even if they never wrote the words "machine learning".
*   **Strict Experience Brackets:** Searching for *"junior under 2 years"* or *"senior between 5-8 years"*. The AI parses these brackets and screens out over-qualified or under-qualified candidates.
*   **Pasting Job Roles:** Pasting a short sentence from a client's job requirements.

### When It Fails / Underperforms:
*   **No Internet / Expired Keys:** If the system has no internet connection or the Groq API key is invalid, it will fail or fall back to the simple search.
*   **High-Speed Autocomplete:** It is too slow (taking 300ms–800ms) to update results dynamically with every keypress.
