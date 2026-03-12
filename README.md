# Task 2 – Environment Configuration and GitHub Integration

## Overview

In this task, I enhanced the existing **Tea Maker Streamlit application** by learning GitHub basics and implementing environment variable configuration for sensitive data.

---

## Task 1: Learn Basic GitHub Commands

I learned and practiced the following Git commands using **Visual Studio Code**:

* `git init` – Initialize a Git repository
* `git status` – Check repository status
* `git add .` – Add files to staging area
* `git commit -m "message"` – Commit changes
* `git checkout -b branch_name` – Create and switch to a new branch
* `git push -u origin branch_name` – Push code to GitHub repository

I created a new branch called **task2** and pushed the project files to the repository.

---

## Task 2: Configure Database Values Using Environment Variables

Previously, the database connection details were hardcoded in the code.
In this task, I improved security by using environment variables.

### Steps Implemented

1. Created a **.env file** to store sensitive configuration values:

   * MongoDB URL
   * Database name
   * Collection name
   * API key

2. Used the **python-dotenv** package to load environment variables into the application.

3. Accessed environment variables in Python using:

```
os.getenv("VARIABLE_NAME")
```

4. Updated the database connection code to use environment variables instead of hardcoded values.

---

## Security Best Practice

The `.env` file contains sensitive information, so it was excluded from version control by adding it to the **.gitignore** file.

```
.env
```

This ensures that sensitive data is not uploaded to GitHub.

---

## Project Files

```
database.py        -> Streamlit application with MongoDB connection
requirements.txt   -> Project dependencies
.gitignore         -> Prevents sensitive files from being pushed
.env               -> Environment variables (not pushed to GitHub)
```

---

## Technologies Used

* Python
* Streamlit
* MongoDB
* PyMongo
* python-dotenv
* Git & GitHub

---

## Outcome

This task helped me learn how to:

* Use Git and GitHub for version control
* Create and manage branches
* Secure sensitive configuration using `.env`
* Connect a Streamlit application with MongoDB using environment variables
