from typing import Any

ALLOWED_TYPES = {
    "application/pdf": "pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "docx",
    "application/msword": "docx",
    "application/octet-stream": "docx",
    "application/zip": "docx",
    "text/plain": "txt",
}

ALLOWED_EXTENSIONS = {
    "pdf": "pdf",
    "docx": "docx",
    "txt": "txt",
}

SEARCHABLE_SKILLS = [
    "python", "fastapi", "django", "flask", "angular", "react", "vue",
    "mongodb", "sql", "postgresql", "mysql", "docker", "aws", "azure",
    "kubernetes", "java", "node", "typescript", "javascript", "golang",
    "rust", "c++", "machine learning", "deep learning", "tensorflow", "pytorch",
]

SKILL_GROUPS = [
    {"python", "fastapi", "django", "flask", "machine learning", "deep learning", "tensorflow", "pytorch"},
    {"angular", "react", "vue", "javascript", "typescript", "node"},
    {"mongodb", "sql", "postgresql", "mysql"},
    {"docker", "aws", "azure", "kubernetes"},
    {"java", "golang", "rust", "c++"}
]

DEFAULT_PROFILE: dict[str, Any] = {
    "name": "Unknown",
    "age": "Not specified",
    "experience": "fresher",
    "skills": [],
    "role": "Not specified",
    "job_roles": [],
}

QUERY_PARSING_PROMPT = """You are an expert recruiter parsing natural language job search queries.
Parse the user query and extract search filters.
Return ONLY valid JSON with this exact schema:
{
  "skills": ["string"],
  "min_experience_years": number or null,
  "max_experience_years": number or null,
  "role_keyword": "string" or null,
  "requests_resumes": boolean
}

Rules:
- skills: Extract technical skills mentioned (lowercase, deduplicated). Check against: python, fastapi, django, flask, angular, react, vue, mongodb, sql, postgresql, mysql, docker, aws, azure, kubernetes, java, node, typescript, javascript, golang, rust, c++, machine learning, deep learning, tensorflow, pytorch
- min_experience_years: Extract minimum experience requirement (e.g., "2 years" -> 2)
- max_experience_years: Set to null unless explicitly stated (e.g., "2-5 years" -> max is 5)
- role_keyword: Extract the main job title or role (e.g., "python developer", "frontend engineer", "data scientist"). It must represent a full job title/role (e.g., use "frontend developer" instead of just "frontend"). Set to null if none is found.
- requests_resumes: Set to true ONLY if the user explicitly asks to "show", "see", "display", or "view" the resumes/candidates/cards. (e.g. "show me the resumes", "display them", "let me see them"). If they just search or ask a question (e.g. "Find me a python developer"), set this to false.

Examples:
- "Python developer with 2 years experience" -> {"skills": ["python"], "min_experience_years": 2, "max_experience_years": null, "role_keyword": "python developer", "requests_resumes": false}
- "Show me their resumes" -> {"skills": [], "min_experience_years": null, "max_experience_years": null, "role_keyword": null, "requests_resumes": true}
"""

EXTRACTION_PROMPT = """You are an expert resume parser.
Extract structured candidate information from the resume text below.
Return ONLY valid JSON with this exact schema:
{
  "name": "string",
  "age": "string",
  "experience": "string",
  "skills": ["string"],
  "role": "string",
  "job_roles": ["string"]
}

Rules:
- If a field is missing, use "Not specified" except:
  - name -> "Unknown"
  - experience -> "fresher"
  - skills -> []
  - job_roles -> []
- skills must be lowercase, deduplicated, and relevant.
- experience should be a concise string like "3 years" or "fresher".
- job_roles should be readable titles such as "Backend Developer at ABC Corp (2021-2024)".
"""

JOB_RECOMMENDATION_PROMPT = """You are a senior technical recruiter.
Suggest exactly 5 job titles that best match this candidate.
Return ONLY a JSON array of 5 strings.

Candidate:
- Name: {name}
- Experience: {experience}
- Skills: {skills}
- Current Role: {role}
- Previous Roles: {job_roles}
"""
