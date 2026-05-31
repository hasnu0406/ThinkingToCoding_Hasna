# Angular Frontend

This Angular app is intentionally limited to:

- rendering backend responses
- collecting user input
- uploading resumes
- triggering REST API calls

All resume parsing, information extraction, AI processing, candidate recommendation, and job description generation live in the FastAPI backend.

## Run

```bash
npm install
npm start
```

The UI expects the FastAPI server at `http://127.0.0.1:8000`.
