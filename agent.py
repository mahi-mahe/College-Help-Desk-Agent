"""College Help Desk: two CrewAI agents (Administration, Fees) on Groq, data from SQLite.

Flow: student query -> route() picks an agent -> that agent calls its 2 tools
(which read/write college.db) -> answer.
"""
import os
import re
import sqlite3
import sys

from dotenv import load_dotenv

load_dotenv()
os.environ.setdefault("CREWAI_DISABLE_TELEMETRY", "true")

from crewai import Agent, Crew, LLM, Process, Task  # noqa: E402
from crewai.tools import tool  # noqa: E402

# Some CrewAI versions add a 'cache_breakpoint' field to messages; Groq rejects it.
try:
    import crewai.llms.cache as _cache  # noqa: E402

    _cache.mark_cache_breakpoint = lambda msg: msg
except (ImportError, AttributeError):
    pass

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "college.db")
llm = LLM(
    model="groq/" + os.getenv("GROQ_MODEL", "openai/gpt-oss-120b"),
    api_key=os.getenv("GROQ_API_KEY"),
    temperature=0.2,
)


def run_sql(sql, params=()):
    """Run one SQL statement; return (rows, last inserted id)."""
    con = sqlite3.connect(DB_PATH)
    try:
        cur = con.execute(sql, params)
        con.commit()
        return cur.fetchall(), cur.lastrowid
    finally:
        con.close()


# ---------- Administration tools ----------
@tool("get_exam_schedule")
def get_exam_schedule(semester: str) -> str:
    """Return exam dates for a semester, e.g. 'semester 1'."""
    rows, _ = run_sql(
        "SELECT subject, date, time, venue FROM exams WHERE lower(semester)=lower(?) ORDER BY date",
        (semester.strip(),),
    )
    if not rows:
        return f"No exams found for '{semester}'."
    return "\n".join(f"{s}: {d} at {t}, {v}" for s, d, t, v in rows)


@tool("get_timetable")
def get_timetable(day: str) -> str:
    """Return the class timetable for a weekday, e.g. 'monday'."""
    rows, _ = run_sql(
        "SELECT period, subject FROM timetable WHERE lower(day)=lower(?) ORDER BY period",
        (day.strip(),),
    )
    if not rows:
        return f"No classes found for '{day}'."
    return "\n".join(f"{p}: {s}" for p, s in rows)


# ---------- Fees tools ----------
@tool("get_fee_status")
def get_fee_status(student_id: str) -> str:
    """Return total, paid and pending fees for a student ID, e.g. 'S1001'."""
    rows, _ = run_sql(
        "SELECT name, total_fee, paid, due_date FROM students WHERE student_id=?",
        (student_id.strip().upper(),),
    )
    if not rows:
        return f"No student found with ID '{student_id}'."
    name, total, paid, due = rows[0]
    return (f"{name}: total Rs.{total}, paid Rs.{paid}, pending Rs.{total - paid}, "
            f"due date {due or 'none'}")


@tool("raise_fee_ticket")
def raise_fee_ticket(student_id: str, issue: str) -> str:
    """Raise a ticket for a fee or billing problem. Needs the student ID and the issue."""
    sid = student_id.strip().upper()
    found, _ = run_sql("SELECT 1 FROM students WHERE student_id=?", (sid,))
    if not found:
        return f"No student found with ID '{student_id}'. Ticket not created."
    _, ticket_id = run_sql("INSERT INTO tickets (student_id, issue) VALUES (?, ?)", (sid, issue))
    return f"Ticket #{ticket_id} created for {sid}. The accounts office will reply in 3 working days."


# ---------- Agents ----------
Administration_agent = Agent(
    role="Administration Assistant",
    goal="Answer student questions about exams and the class timetable.",
    backstory="You work at the college administration desk. Use your tools; never invent dates.",
    tools=[get_exam_schedule, get_timetable],
    llm=llm,
    allow_delegation=False,
)

Fees_agent = Agent(
    role="Fees Assistant",
    goal="Answer student questions about fees and raise tickets for billing problems.",
    backstory="You work at the college accounts office. Use your tools; never invent amounts.",
    tools=[get_fee_status, raise_fee_ticket],
    llm=llm,
    allow_delegation=False,
)


# ---------- Orchestration ----------
def route(query, history):
    """Ask the LLM which agent should answer; fall back to keywords if unclear."""
    prompt = (
        "Classify the student query. Reply with one word: ADMIN (exams, timetable, classes) "
        "or FEES (fees, bills, payments, refunds).\n"
        f"Recent chat:\n{history or '(none)'}\nQuery: {query}"
    )
    try:
        match = re.search(r"FEES|ADMIN", str(llm.call(prompt)).upper())
    except Exception:
        match = None
    if match:
        return Fees_agent if match.group(0) == "FEES" else Administration_agent
    fee_words = ("fee", "bill", "pay", "refund", "due", "ticket")
    return Fees_agent if any(w in query.lower() for w in fee_words) else Administration_agent


def answer(query, history=""):
    agent = route(query, history)
    task = Task(
        description=f"Recent chat:\n{history or '(none)'}\n\nStudent query: {query}\n\n"
                    "Use your tools to get facts, then reply briefly and politely. "
                    "If the query is outside your scope, say so.",
        expected_output="A short, accurate answer.",
        agent=agent,
    )
    crew = Crew(agents=[agent], tasks=[task], process=Process.sequential)
    return agent.role, str(crew.kickoff())


def main():
    if not os.getenv("GROQ_API_KEY"):
        sys.exit("GROQ_API_KEY is missing. Add it to .env")
    if not os.path.exists(DB_PATH):
        sys.exit("college.db not found. Run: python setup_db.py")

    print("College Help Desk (type 'exit' to quit)")
    history = ""
    while True:
        try:
            query = input("\nYou: ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not query:
            continue
        if query.lower() in ("exit", "quit"):
            break
        try:
            role, reply = answer(query, history)
        except Exception as exc:
            print(f"Error: {exc}")
            continue
        print(f"\n[{role}] {reply}")
        history = (history + f"Student: {query}\nHelp Desk: {reply}\n")[-2000:]


if __name__ == "__main__":
    main()