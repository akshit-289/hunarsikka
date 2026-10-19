"""HunarSikka: simple local learning platform demonstration."""
import json
import sqlite3
from datetime import datetime

import streamlit as st

from database import (
    connect, create_user, execute, get_user_by_email, init_db, one, rows,
    verify_password,
)

st.set_page_config(page_title="HunarSikka | Money Smart. Skill Ready.", page_icon="📚", layout="wide")
init_db()

st.markdown("""
<style>
:root { --purple:#543477; --ink:#292538; }
.stApp { background: #fffdf9; color: var(--ink); }
section[data-testid="stSidebar"] { background: #f1eafb; }
.hs-hero { padding: 2rem 2.2rem; border-radius: 22px; background: linear-gradient(120deg,#e8ddfb 0%,#fff9ef 58%,#ddf3e7 100%); }
.hs-hero h1 { color: #543477; font-size: 2.7rem; margin-bottom: .3rem; }
.hs-hero p { font-size: 1.08rem; }
.hs-card { background: white; border: 1px solid #eee6f4; border-radius: 16px; padding: 1rem 1.1rem; min-height: 125px; }
.hs-muted { color: #625b70; }
div.stButton > button { border-radius: 12px; }
</style>
""", unsafe_allow_html=True)

LESSON = "Recorded Lectures"
TRAINING = "Free Teacher Training"

QUESTIONS = [
    {"q":"A student has limited money for the week. What is the best first step?", "opts":["Buy wants first", "List essential expenses and available money", "Borrow without planning", "Spend everything equally each day"], "a":1, "why":"A simple budget starts with available money and essential expenses."},
    {"q":"A teacher notices that several students do not understand a topic. What is a useful response?", "opts":["Move on immediately", "Blame the students", "Try another explanation and check understanding", "Give everyone a lower grade"], "a":2, "why":"Changing approach and checking understanding helps identify what students need."},
    {"q":"Which is the clearest lesson objective?", "opts":["Understand everything", "Have a nice class", "Students will list three causes of water pollution", "Teach the chapter"], "a":2, "why":"A useful objective describes an observable learning outcome."},
    {"q":"A student shares an incorrect answer in class. What should a teacher do?", "opts":["Mock the answer", "Invite reasoning and correct the misconception respectfully", "Never ask the student again", "Ignore all answers"], "a":1, "why":"Respectful feedback helps students learn without discouraging participation."},
    {"q":"Which approach is most likely to encourage broad participation?", "opts":["Only call on the fastest students", "Use think-pair-share and invite responses", "Ask no questions", "Reward only perfect answers"], "a":1, "why":"Think-pair-share gives students time to think and rehearse ideas."},
    {"q":"A student receives a suspicious message asking for a password. What should they do?", "opts":["Reply with the password", "Forward it to everyone", "Avoid clicking and report or verify it safely", "Use the same password everywhere"], "a":2, "why":"Never share passwords through suspicious messages; verify through trusted channels."},
    {"q":"What should a teacher consider when planning a group activity?", "opts":["Only the fastest finishers", "A clear task, roles and accessible participation", "No instructions", "A task unrelated to the objective"], "a":1, "why":"Clear roles and accessible tasks support purposeful collaboration."},
    {"q":"Which is an example of constructive feedback?", "opts":["This is terrible", "You are not good at this", "Your example is clear; add evidence to support your conclusion", "Try harder"], "a":2, "why":"Specific feedback recognises a strength and gives an actionable next step."},
    {"q":"A lesson is running short on time. What is the best response?", "opts":["Skip the learning objective", "Prioritise the essential outcome and a brief check", "Rush through every slide", "Cancel all questions"], "a":1, "why":"Prioritising the key outcome preserves learning value."},
    {"q":"What is a good way to assess whether students understood a lesson?", "opts":["Assume silence means understanding", "Use a short exit question or task", "Ask only whether they liked it", "Wait until the end of term"], "a":1, "why":"A short task provides evidence of student understanding."},
    {"q":"Two students disagree during group work. What is a constructive first step?", "opts":["Listen to both and help them agree on next steps", "Immediately punish both", "Ignore the conflict", "Choose a side without listening"], "a":0, "why":"Listening and guiding a respectful resolution supports classroom relationships."},
    {"q":"When choosing a digital teaching tool, what should come first?", "opts":["Its popularity alone", "The learning objective, accessibility and privacy", "How many animations it has", "Whether it collects the most data"], "a":1, "why":"A tool should serve the learning goal and respect users' privacy."},
    {"q":"A student consistently finishes tasks early. What is a useful response?", "opts":["Make them wait every time", "Offer a meaningful extension task", "Give them other students' work to do", "Stop providing feedback"], "a":1, "why":"An extension task can deepen learning without penalising the student."},
    {"q":"What is the main purpose of a lesson plan?", "opts":["Guarantee every class is identical", "Organise learning objectives, activities and assessment", "Avoid adapting to students", "Replace teacher judgement"], "a":1, "why":"A plan gives structure while allowing teachers to adapt as needed."},
    {"q":"A student makes a mistake during a presentation. What response is most helpful?", "opts":["Interrupt and embarrass them", "Allow them to continue and offer supportive feedback", "End the presentation", "Compare them negatively with peers"], "a":1, "why":"Supportive feedback helps build confidence and improve skills."},
]

TRAINING_PATHS = {
    "Graphic Design": {"lesson":"Learn visual hierarchy, contrast, alignment and readable typography.", "objectives":"Use a clear headline; limit fonts; choose colours with sufficient contrast.", "assignment":"Create a promotional poster for a fictional school event.", "example":"School Innovation Day — Date, venue, main activity and a clear call to action."},
    "Presentation Making": {"lesson":"Structure a presentation around one clear message and a logical story.", "objectives":"Use concise slide text; make headings meaningful; support claims with examples.", "assignment":"Create an outline for a short presentation introducing an entrepreneurial idea.", "example":"Problem → Proposed solution → Intended audience → Next step."},
    "Creative Writing": {"lesson":"Develop a clear idea, organise details and edit for the intended audience.", "objectives":"Use specific language; organise ideas; check clarity and spelling.", "assignment":"Write a product description or promotional message for a fictional product.", "example":"Describe what the product does, who it helps and one useful benefit."},
}


def current_user():
    uid = st.session_state.get("user_id")
    if not uid:
        return None
    return one("SELECT id,name,email,role,approved FROM users WHERE id=?", (uid,))


def logout():
    for key in ("user_id", "page", "quiz_answers", "last_quiz_result", "budget_result"):
        st.session_state.pop(key, None)
    st.rerun()


def require_role(user, roles):
    if not user or user["role"] not in roles:
        st.warning("Please log in with an account that has permission to access this page.")
        return False
    return True


def heading(title, subtitle=None):
    st.title(title)
    if subtitle:
        st.caption(subtitle)


def login_form(role):
    heading(f"{role.title()} Login", "Welcome back to HunarSikka.")
    with st.form(f"login_{role}"):
        email = st.text_input("Email address")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Log in", type="primary", use_container_width=True)
    if submitted:
        user = get_user_by_email(email)
        if not user or not verify_password(password, user["password_hash"]):
            st.error("Email or password is incorrect.")
        elif user["role"] != role:
            st.error(f"This account is not a {role} account. Choose the correct login page.")
        elif role == "teacher" and not user["approved"]:
            st.warning("Your teacher account is awaiting administrator approval.")
        elif role == "admin" and not user["approved"]:
            st.error("This administrator account is disabled.")
        else:
            st.session_state.user_id = user["id"]
            st.session_state.page = "Dashboard"
            st.rerun()


def register_form(role):
    heading(f"Create a {'Student' if role == 'student' else 'Teacher'} Account")
    if role == "teacher":
        st.info("Teacher accounts require approval by the local administrator before login is enabled.")
    with st.form(f"register_{role}"):
        name = st.text_input("Name or display name")
        email = st.text_input("Email address")
        password = st.text_input("Password", type="password")
        confirm = st.text_input("Confirm password", type="password")
        submitted = st.form_submit_button("Create account", type="primary", use_container_width=True)
    if submitted:
        if not name.strip() or not email.strip() or "@" not in email:
            st.error("Enter a name and a valid email address.")
        elif len(password) < 8:
            st.error("Use a password with at least 8 characters.")
        elif password != confirm:
            st.error("The passwords do not match.")
        else:
            try:
                create_user(name, email, password, role)
                if role == "teacher":
                    st.success("Teacher account created. Ask the administrator to approve it before logging in.")
                else:
                    st.success("Account created. You can now log in.")
            except sqlite3.IntegrityError:
                st.error("An account with this email already exists.")


def public_home():
    st.markdown("""
    <div class="hs-hero">
      <h1>HunarSikka</h1>
      <p><b>Money Smart. Skill Ready.</b></p>
      <p>HunarSikka connects students with learning opportunities and empowers teachers to grow through accessible training, teaching assessments and collaborative learning sessions.</p>
      <p><b>Learn → Practise → Build</b></p>
    </div>
    """, unsafe_allow_html=True)
    st.write("")
    cols = st.columns(3)
    for col, title, desc in zip(cols, ["📚 Learn", "🧠 Practise", "🚀 Build"], ["Explore recorded lessons and learning resources.", "Try practical activities and teacher self-assessments.", "Save projects and track your progress."]):
        with col:
            st.markdown(f'<div class="hs-card"><h3>{title}</h3><p>{desc}</p></div>', unsafe_allow_html=True)
    st.subheader("Explore HunarSikka")
    cols = st.columns(3)
    features = [("Recorded Lectures", "Sample lessons for students."), ("Live Lab", "See session details and coordination."), ("Free Teacher Training", "Practical teacher-development pathways.")]
    for col, (title, desc) in zip(cols, features):
        with col:
            st.markdown(f'<div class="hs-card"><h4>{title}</h4><p>{desc}</p></div>', unsafe_allow_html=True)
    st.subheader("Get started")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.button("Student sign up", key="home_student_signup", type="primary", use_container_width=True, on_click=navigate_to, args=("Student Sign Up", "public_nav"))
    with c2:
        st.button("Student login", key="home_student_login", use_container_width=True, on_click=navigate_to, args=("Student Login", "public_nav"))
    with c3:
        st.button("Teacher login", key="home_teacher_login", use_container_width=True, on_click=navigate_to, args=("Teacher Login", "public_nav"))
    st.caption("Demonstration project: sample content is illustrative and is not a claim of accreditation or institutional partnership.")


def lessons_page(user):
    heading(LESSON, "Sample educational resources. Add approved video links when ready.")
    lessons = rows("SELECT * FROM lessons ORDER BY category,title")
    completed = {r[0] for r in rows("SELECT lesson_id FROM completions WHERE user_id=?", (user["id"],))} if user and user["role"] == "student" else set()
    for lesson in lessons:
        with st.container(border=True):
            a, b = st.columns([4, 1])
            with a:
                st.subheader(lesson["title"])
                st.caption(f"{lesson['category']} · {lesson['duration']}")
                st.write(lesson["description"])
                if lesson["url"]:
                    st.link_button("Open lesson resource", lesson["url"])
                else:
                    st.caption("Demo lesson: add a legally embeddable resource URL when available.")
            with b:
                if user and user["role"] == "student":
                    is_done = lesson["id"] in completed
                    if is_done:
                        st.success("Completed")
                    elif st.button("Mark complete", key=f"lesson_{lesson['id']}"):
                        execute("INSERT OR IGNORE INTO completions(user_id,lesson_id) VALUES(?,?)", (user["id"], lesson["id"]))
                        st.rerun()
    if not lessons:
        st.info("No lessons have been added yet.")


def training_page(user):
    heading(TRAINING, "Free learning pathways for teachers.")
    modules = rows("SELECT * FROM training ORDER BY id")
    done = {r[0] for r in rows("SELECT training_id FROM training_completions WHERE user_id=?", (user["id"],))} if user and user["role"] == "teacher" else set()
    if user and user["role"] == "teacher":
        st.progress(len(done) / max(1, len(modules)), text=f"Completed {len(done)} of {len(modules)} modules")
    for mod in modules:
        with st.expander(f"{mod['title']} · {mod['duration']}"):
            st.write(mod["description"])
            st.markdown("**Learning objectives**")
            st.write(mod["objectives"])
            st.markdown("**Practical activity**")
            st.write(mod["activity"])
            if mod["url"]:
                st.link_button("Open resource", mod["url"])
            if user and user["role"] == "teacher":
                if mod["id"] in done:
                    st.success("Completed")
                elif st.button("Mark as completed", key=f"train_{mod['id']}"):
                    execute("INSERT OR IGNORE INTO training_completions(user_id,training_id) VALUES(?,?)", (user["id"], mod["id"]))
                    st.rerun()
    if not user or user["role"] != "teacher":
        st.info("Teacher login is needed to save training progress.")


def quiz_page(user):
    heading("Teacher Aptitude Test", "Educational self-assessment only — not a certification or employment screening test.")
    if not require_role(user, ["teacher"]):
        return
    if "quiz_answers" not in st.session_state:
        st.session_state.quiz_answers = {}
    with st.form("aptitude_quiz"):
        answers = {}
        for i, q in enumerate(QUESTIONS):
            st.markdown(f"**Question {i+1} of {len(QUESTIONS)}**")
            st.write(q["q"])
            answers[str(i)] = st.radio("Choose one answer", q["opts"], index=None, key=f"q_{i}", label_visibility="collapsed")
            st.divider()
        submitted = st.form_submit_button("Submit assessment", type="primary", use_container_width=True)
    if submitted:
        missing = [i for i, a in answers.items() if a is None]
        if missing:
            st.error(f"Please answer all {len(QUESTIONS)} questions before submitting.")
        else:
            answer_indexes = [q["opts"].index(answers[str(i)]) for i, q in enumerate(QUESTIONS)]
            score = sum(answer_indexes[i] == q["a"] for i, q in enumerate(QUESTIONS))
            execute("INSERT INTO attempts(user_id,score,total,answers_json) VALUES(?,?,?,?)", (user["id"], score, len(QUESTIONS), json.dumps(answer_indexes)))
            st.session_state.last_quiz_result = {"score": score, "answers": answer_indexes}
    result = st.session_state.get("last_quiz_result")
    if result:
        score = result["score"]
        pct = round(score / len(QUESTIONS) * 100)
        st.subheader("Your result")
        st.metric("Score", f"{score} / {len(QUESTIONS)}", f"{pct}%")
        st.progress(pct / 100)
        if pct >= 80:
            st.write("You showed strength across this sample assessment. Keep building on it with practical reflection.")
        elif pct >= 55:
            st.write("You have a useful starting point. Review the explanations below and choose a training module to practise.")
        else:
            st.write("Treat this as a learning opportunity. Review the explanations and practise one skill at a time.")
        for i, q in enumerate(QUESTIONS):
            correct = result["answers"][i] == q["a"]
            with st.expander(f"Question {i+1}: {'Correct' if correct else 'Review this answer'}"):
                st.write(q["q"])
                st.write(f"**Suggested answer:** {q['opts'][q['a']]}")
                st.write(q["why"])
    st.subheader("Previous attempts")
    attempts = rows("SELECT score,total,created_at FROM attempts WHERE user_id=? ORDER BY id DESC", (user["id"],))
    if attempts:
        st.dataframe([{"Score": f"{a['score']}/{a['total']}", "Percentage": f"{round(a['score']/a['total']*100)}%", "Date": a["created_at"]} for a in attempts], use_container_width=True, hide_index=True)
    else:
        st.caption("Your saved attempts will appear here.")


def skill_studio(user):
    heading("Skill Studio", "Learn a practical skill, complete an assignment and save it to your portfolio.")
    pathway = st.selectbox("Choose a pathway", list(TRAINING_PATHS))
    data = TRAINING_PATHS[pathway]
    st.subheader("Mini lesson")
    st.write(data["lesson"])
    st.markdown("**Learning objectives**")
    st.write(data["objectives"])
    st.markdown("**Assignment**")
    st.write(data["assignment"])
    st.markdown("**Example**")
    st.info(data["example"])
    if not require_role(user, ["student"]):
        return
    with st.form("project_create"):
        title = st.text_input("Project title")
        description = st.text_area("Your work", height=160, placeholder="Write your ideas or submission here...")
        submitted = st.form_submit_button("Save to My Portfolio", type="primary")
    if submitted:
        if not title.strip() or not description.strip():
            st.error("Enter a project title and your work before saving.")
        else:
            execute("INSERT INTO projects(user_id,title,pathway,description) VALUES(?,?,?,?)", (user["id"], title.strip(), pathway, description.strip()))
            st.success("Project saved to your private portfolio.")


def portfolio_page(user):
    heading("My Portfolio", "Your saved work is private to your account.")
    if not require_role(user, ["student"]):
        return
    projects = rows("SELECT * FROM projects WHERE user_id=? ORDER BY updated_at DESC,id DESC", (user["id"],))
    if not projects:
        st.info("No projects yet. Visit Skill Studio to create your first project.")
        return
    for p in projects:
        with st.expander(f"{p['title']} · {p['pathway']}"):
            with st.form(f"edit_project_{p['id']}"):
                title = st.text_input("Project title", value=p["title"])
                pathway = st.selectbox("Pathway", list(TRAINING_PATHS), index=list(TRAINING_PATHS).index(p["pathway"]) if p["pathway"] in TRAINING_PATHS else 0)
                desc = st.text_area("Your work", value=p["description"], height=140)
                c1, c2 = st.columns(2)
                with c1:
                    save = st.form_submit_button("Save changes")
                with c2:
                    delete = st.form_submit_button("Delete project")
            if save:
                if title.strip() and desc.strip():
                    execute("UPDATE projects SET title=?,pathway=?,description=?,updated_at=CURRENT_TIMESTAMP WHERE id=? AND user_id=?", (title.strip(), pathway, desc.strip(), p["id"], user["id"]))
                    st.success("Project updated.")
                    st.rerun()
                else:
                    st.error("Title and work cannot be empty.")
            if delete:
                execute("DELETE FROM projects WHERE id=? AND user_id=?", (p["id"], user["id"]))
                st.success("Project deleted.")
                st.rerun()


def live_lab(user):
    heading("Live Lab", "Simple session coordination — not a built-in video conferencing service.")
    sessions = rows("SELECT * FROM sessions ORDER BY starts_at")
    if user and user["role"] == "teacher":
        with st.expander("Propose a session"):
            with st.form("new_session"):
                title = st.text_input("Session topic")
                desc = st.text_area("Description")
                when = st.text_input("Proposed date and time", placeholder="2026-11-15 16:00")
                submit = st.form_submit_button("Submit proposal")
            if submit:
                try:
                    datetime.strptime(when.strip(), "%Y-%m-%d %H:%M")
                    if not title.strip() or not desc.strip():
                        st.error("Enter a topic and description.")
                    else:
                        execute("INSERT INTO sessions(title,description,starts_at,status,created_by) VALUES(?,?,?,?,?)", (title.strip(), desc.strip(), when.strip(), "Proposed", user["id"]))
                        st.success("Session proposal saved.")
                        st.rerun()
                except ValueError:
                    st.error("Use the format YYYY-MM-DD HH:MM.")
    if not sessions:
        st.info("No sessions are currently listed.")
    for s in sessions:
        with st.container(border=True):
            st.subheader(s["title"])
            session_status = (s["status"] or "").strip()
            meeting_url = (s["meeting_url"] or "").strip()
            is_scheduled = session_status.casefold() == "scheduled"
            st.caption(f"{s['starts_at']} · Status: {session_status or 'Awaiting Confirmation'}")
            st.write(s["description"])
            if meeting_url and is_scheduled:
                st.link_button("Open Google Meet / session meeting", meeting_url, use_container_width=True)
            elif user and user["role"] == "student" and meeting_url and not is_scheduled:
                st.info("A meeting link has been added, but it will appear when the teacher changes the session status to Scheduled.")
            elif session_status != "Completed":
                st.caption("The meeting link will appear here after the session is marked Scheduled and the link is saved in Session management → Meeting URL.")
            if user and user["role"] == "student" and s["status"] in ("Scheduled", "Awaiting Confirmation"):
                registered = one("SELECT 1 FROM registrations WHERE user_id=? AND session_id=?", (user["id"], s["id"]))
                if registered:
                    st.success("You are registered")
                elif st.button("Register / RSVP", key=f"rsvp_{s['id']}"):
                    execute("INSERT OR IGNORE INTO registrations(user_id,session_id) VALUES(?,?)", (user["id"], s["id"]))
                    st.rerun()
            if user and user["role"] in ("teacher", "admin"):
                with st.expander("Session management"):
                    status_options = ["Proposed", "Awaiting Confirmation", "Scheduled", "Completed", "Cancelled"]
                    saved_status = (s["status"] or "Awaiting Confirmation").strip()
                    status_index = next((i for i, option in enumerate(status_options) if option.casefold() == saved_status.casefold()), 1)
                    status = st.selectbox("Status", status_options, index=status_index, key=f"status_{s['id']}")
                    st.caption("Paste the official Google Meet URL in this field. A link written in the discussion is not treated as the official meeting link.")
                    meeting = st.text_input("Meeting URL (visible to students when status is Scheduled)", value=(s["meeting_url"] or ""), key=f"url_{s['id']}")
                    if st.button("Save session", key=f"save_session_{s['id']}"):
                        if meeting and not meeting.startswith(("https://", "http://")):
                            st.error("Meeting URL must begin with https:// or http://")
                        else:
                            execute("UPDATE sessions SET status=?,meeting_url=? WHERE id=?", (status, meeting.strip(), s["id"]))
                            st.success("Session updated.")
                            st.rerun()
            if user:
                st.markdown("**Session discussion**")
                posts = rows("SELECT posts.message,posts.created_at,users.name,users.role FROM posts JOIN users ON users.id=posts.user_id WHERE posts.session_id=? ORDER BY posts.id", (s["id"],))
                for post in posts:
                    st.caption(f"{post['name']} ({post['role']}) · {post['created_at']}")
                    st.write(post["message"])
                with st.form(f"post_{s['id']}"):
                    message = st.text_input("Add a session-related message", max_chars=500)
                    post_submit = st.form_submit_button("Post message")
                if post_submit:
                    if message.strip():
                        execute("INSERT INTO posts(session_id,user_id,message) VALUES(?,?,?)", (s["id"], user["id"], message.strip()))
                        st.rerun()
                    else:
                        st.error("Enter a message first.")
    if user and user["role"] == "admin":
        st.subheader("Session registrations")
        regs = rows("SELECT sessions.title,users.name,users.email,registrations.created_at FROM registrations JOIN sessions ON sessions.id=registrations.session_id JOIN users ON users.id=registrations.user_id ORDER BY registrations.created_at DESC")
        if regs:
            st.dataframe([dict(r) for r in regs], use_container_width=True, hide_index=True)
        else:
            st.caption("No registrations yet.")


def navigate_to(page, nav_key):
    """Change the selected sidebar page from a call-to-action button."""
    st.session_state[nav_key] = page


def money_lab(user):
    heading("Money Smart Lab", "Practise making a simple weekly budget with fictional amounts.")
    st.info("This is a learning simulator, not a bank account or financial advice. Use sample amounts only.")
    if not require_role(user, ["student"]):
        return
    with st.form("budget_simulator"):
        allowance = st.number_input("Money available this week (₹)", min_value=0, max_value=100000, value=1000, step=50)
        needs = st.number_input("Needs — transport, food, school supplies (₹)", min_value=0, max_value=100000, value=500, step=50)
        wants = st.number_input("Wants — treats, games, shopping (₹)", min_value=0, max_value=100000, value=200, step=50)
        savings = st.number_input("Savings goal (₹)", min_value=0, max_value=100000, value=200, step=50)
        submitted = st.form_submit_button("Calculate my budget", type="primary", use_container_width=True)
    if submitted:
        total = needs + wants + savings
        remaining = allowance - total
        st.session_state.budget_result = {"allowance": allowance, "needs": needs, "wants": wants, "savings": savings, "remaining": remaining}
        execute("INSERT INTO budget_runs(user_id,allowance,needs,wants,savings) VALUES(?,?,?,?,?)", (user["id"], allowance, needs, wants, savings))
    result = st.session_state.get("budget_result")
    if result:
        a, b, c = st.columns(3)
        a.metric("Needs", f"₹{result['needs']:,.0f}")
        b.metric("Wants", f"₹{result['wants']:,.0f}")
        c.metric("Savings goal", f"₹{result['savings']:,.0f}")
        remaining = result["remaining"]
        if remaining < 0:
            st.error(f"Your plan is ₹{abs(remaining):,.0f} over budget. Reduce wants first or adjust the plan.")
        else:
            st.success(f"You have ₹{remaining:,.0f} left after this plan.")
            if result["allowance"] and result["savings"] / result["allowance"] >= 0.2:
                st.write("Good start: your savings goal is at least 20% of the money available.")
            elif result["allowance"]:
                st.write("Try reviewing whether you can set aside a little more for savings after covering needs.")
        st.caption("Learning tip: cover essential needs first, plan wants intentionally, and choose a realistic savings goal.")
    st.subheader("Your previous budget exercises")
    history = rows("SELECT allowance,needs,wants,savings,created_at FROM budget_runs WHERE user_id=? ORDER BY id DESC LIMIT 5", (user["id"],))
    if history:
        st.dataframe([{"Date": r["created_at"], "Available": f"₹{r['allowance']:,.0f}", "Needs": f"₹{r['needs']:,.0f}", "Wants": f"₹{r['wants']:,.0f}", "Savings goal": f"₹{r['savings']:,.0f}", "Balance": f"₹{r['allowance']-r['needs']-r['wants']-r['savings']:,.0f}"} for r in history], use_container_width=True, hide_index=True)
    else:
        st.caption("Your saved budget exercises will appear here.")


def dashboard(user):
    heading(f"Welcome, {user['name']}!", f"Your {user['role']} dashboard")
    if user["role"] == "student":
        total = one("SELECT COUNT(*) n FROM lessons")["n"]
        done = one("SELECT COUNT(*) n FROM completions WHERE user_id=?", (user["id"],))["n"]
        projects = one("SELECT COUNT(*) n FROM projects WHERE user_id=?", (user["id"],))["n"]
        a, b, c = st.columns(3)
        a.metric("Lessons completed", f"{done}/{total}")
        b.metric("Portfolio projects", projects)
        c.metric("Learning progress", f"{round(done/max(1,total)*100)}%")
        st.progress(done / max(1, total))
        st.write("Continue with a recorded lesson, practise a skill or review your portfolio.")
        q1, q2, q3 = st.columns(3)
        q1.button("Open lessons", use_container_width=True, on_click=navigate_to, args=("Recorded Lectures", "logged_nav"))
        q2.button("Practise a skill", use_container_width=True, on_click=navigate_to, args=("Skill Studio", "logged_nav"))
        q3.button("View portfolio", use_container_width=True, on_click=navigate_to, args=("My Portfolio", "logged_nav"))
    elif user["role"] == "teacher":
        latest = one("SELECT score,total,created_at FROM attempts WHERE user_id=? ORDER BY id DESC LIMIT 1", (user["id"],))
        done = one("SELECT COUNT(*) n FROM training_completions WHERE user_id=?", (user["id"],))["n"]
        a, b = st.columns(2)
        a.metric("Training modules completed", f"{done}/6")
        b.metric("Latest aptitude result", f"{latest['score']}/{latest['total']}" if latest else "Not attempted")
        st.write("Take the aptitude self-assessment and explore free teacher-training modules.")
        q1, q2 = st.columns(2)
        q1.button("Take aptitude test", use_container_width=True, on_click=navigate_to, args=("Teacher Aptitude Test", "logged_nav"))
        q2.button("Explore training", use_container_width=True, on_click=navigate_to, args=("Free Teacher Training", "logged_nav"))
    else:
        st.write("Use the administrator tools to approve teacher accounts and manage demonstration content.")
        st.metric("Pending teacher approvals", one("SELECT COUNT(*) n FROM users WHERE role='teacher' AND approved=0")["n"])


def admin_page(user):
    heading("Administrator Tools", "Local demonstration controls.")
    if not require_role(user, ["admin"]):
        return
    pending = rows("SELECT id,name,email,created_at FROM users WHERE role='teacher' AND approved=0 ORDER BY created_at")
    st.subheader("Teacher approvals")
    if not pending:
        st.caption("No teacher accounts are waiting for approval.")
    for t in pending:
        c1, c2, c3 = st.columns([3, 2, 1])
        c1.write(f"**{t['name']}**  \n{t['email']}")
        c2.caption(f"Requested: {t['created_at']}")
        if c3.button("Approve", key=f"approve_{t['id']}"):
            execute("UPDATE users SET approved=1 WHERE id=? AND role='teacher'", (t["id"],))
            st.success("Teacher approved.")
            st.rerun()
    st.divider()
    st.subheader("Add a recorded lesson")
    with st.form("add_lesson"):
        title = st.text_input("Lesson title")
        category = st.text_input("Category", value="General")
        desc = st.text_area("Description")
        duration = st.text_input("Duration", value="10 min")
        url = st.text_input("Resource URL (optional)")
        submit = st.form_submit_button("Add lesson")
    if submit:
        if not title.strip() or not desc.strip():
            st.error("Title and description are required.")
        elif url.strip() and not url.startswith(("https://", "http://")):
            st.error("Resource URL must begin with https:// or http://")
        else:
            execute("INSERT INTO lessons(title,category,description,duration,url) VALUES(?,?,?,?,?)", (title.strip(), category.strip() or "General", desc.strip(), duration.strip() or "10 min", url.strip()))
            st.success("Lesson added.")
            st.rerun()
    st.subheader("Current lessons")
    for lesson in rows("SELECT * FROM lessons ORDER BY id"):
        with st.expander(lesson["title"]):
            st.write(lesson["description"])
            st.caption(f"{lesson['category']} · {lesson['duration']}")
            if st.button("Delete lesson", key=f"delete_lesson_{lesson['id']}"):
                execute("DELETE FROM lessons WHERE id=?", (lesson["id"],))
                st.rerun()
    st.divider()
    st.subheader("Feedback received")
    feedback = rows("SELECT name,email,category,message,created_at FROM feedback ORDER BY id DESC")
    if feedback:
        st.dataframe([dict(r) for r in feedback], use_container_width=True, hide_index=True)
    else:
        st.caption("No feedback received yet.")


def contact_page(user):
    heading("Contact / Feedback", "Share a suggestion or report a problem. Please do not include passwords or sensitive personal information.")
    with st.form("feedback_form"):
        name = st.text_input("Name (optional)", value=user["name"] if user else "")
        email = st.text_input("Email (optional)", value=user["email"] if user else "")
        category = st.selectbox("Topic", ["Suggestion", "Question", "Technical issue", "Other"])
        message = st.text_area("Message", max_chars=2000)
        submit = st.form_submit_button("Send feedback", type="primary")
    if submit:
        if not message.strip():
            st.error("Please enter a message.")
        else:
            execute("INSERT INTO feedback(name,email,category,message) VALUES(?,?,?,?)", (name.strip() or "Visitor", email.strip(), category, message.strip()))
            st.success("Thank you. Your feedback has been saved in this local demonstration.")


def static_page(page):
    content = {
        "About Us": ("About HunarSikka", "HunarSikka is a student–teacher learning concept built around accessible learning resources, practical skill development and teacher growth. The platform follows Learn → Practise → Build."),
        "FAQ": ("Frequently Asked Questions", "**Who can register?** Students and teachers can create separate accounts. Teacher accounts require administrator approval.\n\n**Are the teacher tests certifications?** No. They are educational self-assessments only.\n\n**Are training modules paid?** No payment is required in this demonstration.\n\n**Are Live Lab meetings hosted here?** No. Confirmed meetings use an external meeting service.\n\n**Is portfolio work public?** No. It is associated with the student's account."),
        "Privacy Policy": ("Privacy Policy — Demonstration Draft", "This local demo stores account names, email addresses, password hashes, learning progress, assessment results, session registrations, discussion posts and portfolio text in a local SQLite database. Data is used to provide the demonstration features. Portfolio records are shown only to the signed-in owner through the app's queries.\n\nBefore public deployment, this policy must be reviewed and updated to reflect the actual hosting environment, retention, access controls, account deletion process and applicable requirements for teenage users. Do not use real sensitive personal data in this demo."),
        "Terms and Conditions": ("Terms and Conditions — Demonstration Draft", "Use HunarSikka respectfully for educational purposes. Do not post sensitive personal information, abusive content or unauthorised links. Aptitude results are educational guidance only and do not certify teaching ability. Sample content and session details may be illustrative.\n\nThis draft requires review before public deployment and is not legal advice."),
    }
    title, body = content[page]
    heading(title)
    st.markdown(body)


def main():
    user = current_user()
    st.sidebar.markdown("## 📚 HunarSikka")
    st.sidebar.caption("Money Smart. Skill Ready.")
    if user:
        st.sidebar.success(f"{user['name']} · {user['role'].title()}")
        pages = ["Dashboard", "Recorded Lectures", "Live Lab", "About Us", "Contact / Feedback", "FAQ", "Privacy Policy", "Terms and Conditions"]
        if user["role"] == "student":
            pages = ["Dashboard", "Money Smart Lab", "Recorded Lectures", "Live Lab", "Skill Studio", "My Portfolio", "About Us", "Contact / Feedback", "FAQ", "Privacy Policy", "Terms and Conditions"]
        elif user["role"] == "teacher":
            pages = ["Dashboard", "Teacher Aptitude Test", "Free Teacher Training", "Live Lab", "About Us", "Contact / Feedback", "FAQ", "Privacy Policy", "Terms and Conditions"]
        else:
            pages = ["Dashboard", "Administrator Tools", "Recorded Lectures", "Free Teacher Training", "Live Lab", "About Us", "Contact / Feedback", "FAQ", "Privacy Policy", "Terms and Conditions"]
        selected = st.sidebar.radio("Navigate", pages, key="logged_nav")
        if st.sidebar.button("Log out", use_container_width=True):
            logout()
        if selected == "Dashboard": dashboard(user)
        elif selected == "Money Smart Lab": money_lab(user)
        elif selected == "Recorded Lectures": lessons_page(user)
        elif selected == "Free Teacher Training": training_page(user)
        elif selected == "Teacher Aptitude Test": quiz_page(user)
        elif selected == "Skill Studio": skill_studio(user)
        elif selected == "My Portfolio": portfolio_page(user)
        elif selected == "Live Lab": live_lab(user)
        elif selected == "Administrator Tools": admin_page(user)
        elif selected == "Contact / Feedback": contact_page(user)
        else: static_page(selected)
    else:
        pages = ["Home", "Student Login", "Student Sign Up", "Teacher Login", "Teacher Sign Up", "Administrator Login", "Recorded Lectures", "Live Lab", "Free Teacher Training", "Money Smart Lab", "About Us", "Contact / Feedback", "FAQ", "Privacy Policy", "Terms and Conditions"]
        selected = st.sidebar.radio("Navigate", pages, key="public_nav")
        if selected == "Home": public_home()
        elif selected == "Student Login": login_form("student")
        elif selected == "Student Sign Up": register_form("student")
        elif selected == "Teacher Login": login_form("teacher")
        elif selected == "Teacher Sign Up": register_form("teacher")
        elif selected == "Administrator Login": login_form("admin")
        elif selected == "Recorded Lectures": lessons_page(None)
        elif selected == "Live Lab": live_lab(None)
        elif selected == "Free Teacher Training": training_page(None)
        elif selected == "Money Smart Lab":
            heading("Money Smart Lab", "Register as a student to save and review your budget exercises.")
            st.info("This interactive budgeting tool is available after student login.")
            st.button("Student login", key="public_money_login", on_click=navigate_to, args=("Student Login", "public_nav"))
        elif selected == "Contact / Feedback": contact_page(None)
        else: static_page(selected)
        st.sidebar.divider()
        st.sidebar.caption("Administrator access is for the local project owner.")
    st.sidebar.divider()
    st.sidebar.caption("School-project demonstration · Local data storage")


if __name__ == "__main__":
    main()
