# HunarSikka — Local Demo

**Tagline:** Money Smart. Skill Ready.

A deliberately simple local prototype for a Class 12 Entrepreneurship (EMC) project. It uses Streamlit for the interface, Python for application logic, and SQLite for local data storage.

## Requirements

- Python 3.10 or newer (Python 3.11 or 3.12 recommended)
- Internet only to install Streamlit; the app and its SQLite database run locally afterward

## Run on Windows

1. Extract this folder to a location you can write to.
2. Open Command Prompt or PowerShell in the `hunarsikka` folder.
3. Create a virtual environment:

   ```powershell
   py -m venv .venv
   .venv\Scripts\Activate.ps1
   ```

   If PowerShell blocks activation, use Command Prompt and run `.venv\Scripts\activate.bat`, or run `.venv\Scripts\python.exe -m pip install -r requirements.txt` without activating.
4. Install the one external dependency:

   ```powershell
   python -m pip install -r requirements.txt
   ```
5. Start the site:

   ```powershell
   streamlit run app.py
   ```
6. Open the local address shown in the terminal, usually `http://localhost:8501`.

## Run on macOS / Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
streamlit run app.py
```

## Demo accounts

The app creates a local administrator account on first run:

- Email: `admin@hunarsikka.local`
- Password: `ChangeMe123!`

This is only a local demo credential. Change it before any real use. Do not expose this prototype directly to the public internet.

To demonstrate student and teacher workflows:

1. Create a student account from **Student Sign Up**, then log in.
2. Create a teacher account from **Teacher Sign Up**.
3. Log in as the administrator, open **Administrator Tools**, and approve the teacher account.
4. Log out and log in through **Teacher Login**.
5. Try the teacher aptitude assessment, training modules and Live Lab.
6. Log in as a student, open **Money Smart Lab**, calculate a budget and confirm the exercise appears in history.
7. Mark a lesson complete, save a Skill Studio project, log out and back in, and confirm the saved records remain.

## Data storage and reset

The database is created automatically as `hunarsikka.db` in this folder. It stores accounts, progress, quiz attempts, sessions, registrations, discussion posts, portfolio projects and feedback. Back up the file if you want to preserve the demo data.

To reset all local data, stop Streamlit and delete `hunarsikka.db`. The next launch recreates the database and sample content. This deletes all accounts and saved work.

## Included features

- Home page and public information pages
- Separate student and teacher registration/login flows
- Password hashing using Python's standard library
- Teacher account approval by a local administrator
- Sample recorded lessons and completion tracking
- Fixed 15-question teacher self-assessment with saved attempts and explanations
- Six teacher-training modules and saved completion status
- Skill Studio with three practical pathways
- Private, account-specific text portfolio with edit/delete
- Live Lab session listings, RSVP, status and meeting URL management, and a session discussion board
- Feedback form and basic lesson management
- Student/teacher/admin-specific navigation
- Home-page buttons that navigate to registration/login flows
- Money Smart Lab budget simulator with saved exercise history
- Student/teacher dashboard shortcuts to the main workflows

## Important limitations

- This is a **local school-project prototype**, not a production-ready public platform.
- The SQLite file is local to this computer; data is not synchronised between different computers.
- The prototype's role checks and login flow are suitable only for a controlled local demonstration. Public deployment needs a security review, stronger server-side access enforcement, rate limiting, account recovery, secure deployment configuration and appropriate privacy safeguards.
- No email verification, password reset, real-time chat, file upload, video hosting, Zoom integration or formal teacher certification is implemented.
- This is a local demonstration. Do not expose it directly to the public internet or enter sensitive personal information.
- The sample Live Lab date and lesson content are illustrative. Confirm dates and meeting URLs before presenting them as real sessions.
- Privacy Policy and Terms pages are draft demonstration text and require review before public deployment.
- Use fictional data for the school demonstration; do not enter sensitive personal information.

