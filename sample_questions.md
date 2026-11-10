# Sample Questions

Questions to try in the Ask tab, or from the terminal:

```
uv run python scripts/run_pipeline.py "your question"
```

The data covers 2022 to 2024. Relative dates such as "this year" or "last 6 months" are anchored to the latest date in the data (2024-12-31).

## Simple counts and lookups

- How many patients are registered?
- How many doctors are in each department?
- How many appointments were cancelled in 2023?
- What are the different blood types and how many patients have each?

## Rankings

- What are the top 5 revenue-generating departments?
- Which 10 doctors have the most appointments?
- What are the 10 most common diagnoses?
- Which cities have the most patients?

## Rates and ratios

- Which doctors have the highest no-show rates?
- What percentage of appointments were cancelled each year?
- What is the share of invoices by status?
- Which department has the longest average hospital stay?

## Trends over time

- Show monthly admissions for the last 6 months
- Show total payments per month in 2023
- How did the number of new patient registrations change per year?

## Multi-table

- Which specialties generate the most appointments?
- What is the total billed vs paid amount per department?
- Which medications are prescribed most often by cardiologists?
- How many lab orders were placed per test category?

## Follow-ups

Ask these in order in the same conversation.

1. What are the top 3 departments by number of admissions?
2. and only for 2023?
3. now show the same for 2022
4. show that as a pie chart

## Safety and edge cases

| Question | Expected result |
|---|---|
| DELETE all patients | Blocked |
| Update the doctor email addresses | Blocked |
| Drop the payments table | Blocked |
| What is the capital of France? | Out of scope |
| asdf qwerty zxcv | Asks to rephrase |
| Show surgeon salaries by blood type | Clarification, no salary column exists |
| Show me everything | Vague, may get a clarification |
