# Product Architecture: Why We Have Both Regular Search and Bot Search

From a product design and system engineering perspective, having both searches is a best-practice decision. Here is why both exist in the platform:

---

## 1. Cost Optimization (API Bills)
*   **Regular Search:** Runs entirely on your local server for **free** ($0.00 cost).
*   **AI Bot Search:** Every search query sent to the AI (Groq API) costs a tiny fraction of a cent. 
*   **Why have both:** If a recruiter just wants to find a candidate named "John" or search for the word "Python", using the AI is a waste of money. Having both lets the system use the free, fast search for simple tasks, and reserve the AI search for complex natural language queries.

---

## 2. Latency & Speed (User Experience)
*   **Regular Search:** Returns results in **under 5 milliseconds** (instant).
*   **AI Bot Search:** Requires a round-trip network call to the AI cloud servers, taking **300ms to 800ms**.
*   **Why have both:** For quick typing and autocompletion, recruiters expect instant feedback. For complex sourcing, they are willing to wait a half-second for the AI to understand their query.

---

## 3. High Availability & System Reliability
*   **Regular Search:** Has zero external dependencies. It works offline and will never go down as long as your database is running.
*   **AI Bot Search:** Relies on third-party API servers (Groq), internet connection, and API key credits.
*   **Why have both:** If the Groq API goes down or you hit rate limits, the AI Bot Search will fail. The Regular Search serves as a **safety fallback** so recruiters can keep working.

---

## 4. Different Search Use-Cases
*   **Regular Search:** Built for **Structured Filtering**. Best used when recruiters select checkboxes (e.g., ticking "React" and "3 years exp" from a dropdown list).
*   **AI Bot Search:** Built for **Natural Sourcing**. Best used when recruiters type conversational requests (e.g., *"Find me a senior designer who can join immediately and has worked with React"*).
