# Candidate Search Platform

This project has:

- A FastAPI backend in `main.py`
- An Angular frontend in `frontend/`

## Start The App

Open two terminals in the project root.

Backend:

```bat
start-backend.cmd
```

Frontend:

```bat
start-frontend.cmd
```

Then open:

```text
http://localhost:4200
```

## Manual Commands

If you prefer running the commands yourself:

Backend:

```powershell
.\.venv\Scripts\python.exe main.py
```

Frontend:

```powershell
cd frontend
npm.cmd start
```

## Notes

- The backend listens on `http://127.0.0.1:8000`
- The frontend calls the backend at `http://127.0.0.1:8000`
- MongoDB should be running locally at `mongodb://localhost:27017/`
