# Morning TODO Email

- Send a morning TODO email to broadcast:
  - Issues you will be working on
  - Working hours
  - Blocking issues/PRs

## Goals

- Think about what you are going to work on for the day, so you have a clear plan
- Let Team Leaders know that you are going to work today and what your workload is
- Make sure people blocked on your tasks know whether you are working on them
- Broadcast if you are blocked or if you don't have tasks
- Replace stand-up meetings

## When to Send

- Send the email within the first hour of beginning the day
  - There is no hard deadline, since people work from different time zones
  - Doing it first thing in the morning ensures that you don't forget
- Check your inbox (email, GitHub) first, so that the plan for the day reflects all
  the updates

## Recipients and Subject

- Send the email to:
  - Permanent team members and people on a 3-month trial: `eng@...`
  - Interns and collaborators: `contributors@...`
- Use the subject `TODO` (all caps), to make it easier to filter emails by subject
- Reply to your previous TODO email, so that at least the last week of TODOs is
  included

## Email Content

### Working Hours

- Specify how many hours you are going to work today
- On Monday, also estimate the hours for the week
- An approximation is enough

### Task List

- List all the tasks you are going to work on during the day, in priority order
- Add a hyperlink to the corresponding GitHub issue for each task, to ease
  navigation

  <img width="381" src="https://github.com/sorrentum/sorrentum/assets/31514660/0d2fbba4-1e6c-4c39-9c04-7ffc4acdde81">

- Provide an ETA for each task
- Report the blocked PRs/issues

### ETAs

- Always estimate the ETA yourself, based on the task's difficulty, its priority, and
  your workload
- There is no reason to be optimistic: complex things take time to be done correctly
- Use a date in the `YYYY-MM-DD` format, e.g., `2023-05-20`
- When possible, add "today", "yesterday", "tomorrow", or "end of week", so that the
  date is easier to parse
  - "End of week" generally means Friday
  - It can be extended if you plan to work on the weekend (provide the date to
    clarify)
  - If none of these terms applies, it is okay to provide just the date
- If the original ETA has not changed, omit "Original ETA" and "Reason for ETA
  update"
- If the original ETA needs an update (e.g., you expected to finish a task by
  yesterday, but it is taking longer):
  - Keep the older date as "Original ETA"
  - Add the new date as "ETA"

## Template

```text
To: eng@...

Subject: TODO

Hi all,

Today I am going to work XYZ hours

Issues:
- GitHub issue title and number with a hyperlink
   - ETA: YYYY-MM-DD
- GitHub issue title and number with a hyperlink
   - Original ETA: YYYY-MM-DD
   - ETA: YYYY-MM-DD
   - Reason for ETA update: ...
   - Blocked on: ... (ok to omit if not blocked)
```

## Examples

### Good Example

```text
To: eng@...

Subject: TODO

Hi all,

Today I am going to work 8 hours

Issues:
- Create matching service #261
    - ETA: today (2023-05-25)
    - Original ETA: yesterday (2023-05-24)
    - Reason for ETA update: it was more complex than what we thought
    - Blocked on: PR review from Grisha
- Create linear supply/demand curves #177
    - ETA: tomorrow (2023-05-26)
- Unit test `compute_share_prices_and_slippage()` #8482
    - ETA: 2024-06-19
```

### Bad Example

```text
To: eng@...

Subject: to-do

Hi all,

Today I am going to work 2-6 hours.
- Calls
- PR reviews
- Finish the trading report analysis
```
