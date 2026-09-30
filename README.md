# College Help Desk Agent

A small multi-agent chatbot for students, built with CrewAI, Groq and Streamlit. It answers questions using data stored in a SQLite database.

## What it does

- **Administration agent** answers questions about exams and the class timetable.
- **Fees agent** shows fee status and raises tickets for billing problems.
- A router picks the right agent for each question.

## Setup

1. Install Python 3.10 to 3.13.
2. Install the dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Create a `.env` file with your [Groq API key](https://console.groq.com/keys):

   ```env
   GROQ_API_KEY=your-groq-api-key-here
   GROQ_MODEL=openai/gpt-oss-120b
   ```

4. Create the database:

   ```bash
   python setup_db.py
   ```

## Run

Web app:

```bash
streamlit run app.py
```

Terminal chat:

```bash
python agent.py
```

## Example questions

- When is the Machine Learning exam?
- What classes do I have on Friday?
- How much fee does S1003 still have to pay?
- Raise a ticket for S1001: hostel fee charged twice.

## Files

| File | Purpose |
|---|---|
| `agent.py` | Agents, tools and routing |
| `app.py` | Streamlit web interface |
| `setup_db.py` | Creates `college.db` with sample data |
| `requirements.txt` | Python dependencies |
| `.env` | Your API key (do not commit) |

## Troubleshooting

If you see `property 'cache_breakpoint' is unsupported`, run `pip install -U crewai litellm`.

## License

Apache
