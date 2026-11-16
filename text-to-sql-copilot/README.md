# Natural Language Database Copilot (Text-to-SQL)

What if you could ask a database a question the same way you'd ask a coworker? A lot of people at a company need numbers from a database but don't know SQL, so they end up waiting on an analyst to pull it for them. I wanted to see if I could build something that takes a question in plain English, writes the SQL, and gives back the answer, while making sure it can never change or delete anything.

![App screenshot](images/app_screenshot.png)

## How it works

1. You type a question like *"Who are the top 5 customers by total spending?"*
2. The app sends your question plus the database's table structure to an LLM (GPT-OSS 120B through the Groq API), and it writes a SQLite query.
3. Before anything runs, the query goes through a safety check. It has to start with SELECT or WITH, and it gets blocked if it has words like DROP, DELETE, UPDATE, or INSERT anywhere in it, even if someone tries to sneak one in after a semicolon.
4. If it passes, the query runs and you see the SQL it wrote, the results, and how long it took.

On top of the safety check, the database is opened in **read-only mode**, so even if a bad query somehow got through, the database itself would refuse to change. I would say that's the most important part, because you can't fully trust an LLM to always follow the rules you give it. When I tested it by asking it to delete all the orders, the model actually refused on its own, but the app blocked it anyway since the response didn't start with SELECT.

## How I built it

I started in a Jupyter notebook with a tiny database I made myself (5 customers and a handful of orders) just to get the basic flow working: describe the tables to the model, get SQL back, run it. Once that worked I added a second table to see if it could handle joins, then added the safety check, and then turned it into a Streamlit app. After that I switched to the [Chinook database](https://github.com/lerocha/chinook-database), a sample database for a music store with 11 tables, since real questions on it usually need the model to join a few tables together.

## Example questions

| Question | Answer |
|---|---|
| Who are the top 5 customers by total spending? | Helena Holý is #1 at $49.62 |
| What are the top 10 best selling genres? | Rock is way ahead at $826.65 |
| Which sales rep brought in the most revenue? | Jane Peacock at $833.04 |
| Which country has the most customers? | USA with 13 |

Queries run in well under a second since the database is small.

## Run it yourself

1. Get a free API key from [Groq](https://console.groq.com/keys)
2. Make a folder called `.streamlit` and a file inside it called `secrets.toml` with this line:
   ```
   GROQ_API_KEY = "your-key-here"
   ```
3. Install and run:
   ```
   pip install -r requirements.txt
   streamlit run app.py
   ```

## What I'd add next

- Let you ask follow up questions that build on the last answer
- Have the model explain the results in a sentence, not just show the table
- Try it on a bigger, messier database to see where it breaks

**Tools:** Python, SQL (SQLite), Streamlit, Groq API (GPT-OSS 120B), pandas
