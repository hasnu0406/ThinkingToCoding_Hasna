# Simple Guide: What is Swagger UI & What Do These Endpoints Do?

This guide explains the concept of Swagger UI and details what every button in the backend interface actually does.

---

## 1. What is Swagger UI in Simple Words?

Think of **Swagger UI** as an **Interactive Menu** for the backend kitchen. 

Normally, a backend is just invisible code running on a server. Developers would have to write script code just to check if it works. Swagger UI solves this by providing a clean web interface where anyone (including the founder) can look at the available doors (endpoints), type in test data, click **"Try it out"**, and see how the backend responds.

The colored blocks tell you what kind of action is taking place:
*   🔵 **GET (Blue):** Asking the server to *retrieve* information (e.g., "Show me the search history").
*   🟢 **POST (Green):** Sending *new* information to the server (e.g., "Here is a search query, please process it").
*   🟡 **PATCH (Orange):** *Updating* existing information (e.g., "Change this candidate's name").
*   🔴 **DELETE (Red):** *Removing* information permanently (e.g., "Clear all search history").

---

## 2. Explanation of the Endpoints (From the Screenshot)

Here is what each item shown on your Swagger screen does:

### 🔵 `GET /` (Home)
*   **What it does:** Returns a simple message: `{"message": "Candidate Search Platform API v5 is running."}`
*   **Purpose:** A quick test to see if the server is turned on. It is like knocking on the kitchen door to see if the Chef answers.

### 🔵 `GET /health` (Health Check)
*   **What it does:** Returns the status, server timestamp, and whether the AI is active: `{"status": "ok", "groq_available": true}`
*   **Purpose:** Diagnoses if the connection to the AI (Groq) is working properly.

### 🟢 `POST /search` (Regular Search)
*   **What it does:** Accepts a search word and returns matching candidates.
*   **Purpose:** A traditional search engine that uses exact text patterns to find matches.

### 🟢 `POST /search/bot` (AI Bot Search)
*   **What it does:** Accepts natural sentences (e.g., *"I need a Python developer with 3 years experience"*).
*   **Purpose:** This is the smart AI-powered search. It understands context, translates the sentence into search filters, scores candidates, and ranks them from best matching to worst.

### 🔵 `GET /search/history` (Get Search History)
*   **What it does:** Retrieves a list of recent searches that recruiters have performed, including the candidates they were shown.
*   **Purpose:** Keeps a record of previous activity so recruiters can resume their work.

### 🔴 `DELETE /search/history` (Clear Search History)
*   **What it does:** Deletes the logs of all previous search queries.
*   **Purpose:** Clears the database log to keep things tidy.

---

## 3. Other Endpoints in the Code (Scrollable below the screenshot)

These are the candidate and file management buttons located further down the page:

*   🟢 `POST /resume/upload`: Uploads a PDF or Word resume, extracts the text, sends it to the AI to extract candidate data, and creates a database profile.
*   🔵 `GET /resumes`: Lists all candidates saved in the system (with pages/pagination).
*   🔵 `GET /resume/{id}`: Opens one candidate's full profile details.
*   🟡 `PATCH /resume/{id}`: Saves edits made manually by a recruiter (e.g., if they want to update/add a skill).
*   🔴 `DELETE /resume/{id}`: Deletes a candidate profile permanently.
*   🔵 `GET /resume/{id}/recommend`: Asks the AI to refresh the matching job titles for a candidate.
*   🔵 `GET /export/candidates`: Downloads a clean spreadsheet (`.csv` file) of all candidates in the system.
