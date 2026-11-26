# Morning TODO Email

The idea is to send a morning TODO email to broadcast:

- Issues you will be working on
- Working hours
- Blocking issues/PRs

- E-mail template:
  ```
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

- Good example:
  ```
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

- Bad example:
  ```
  To: eng@...

  Subject: to-do

  Hi all,

  Today I am going to work 2-6 hours.
  - Calls
  - PR reviews
  - Finish the trading report analysis
  ```

- The goal is:
  - Think about what you are going to work on for the day, so you have a clear
    plan
  - Let Team Leaders know that you're going to work today and what is your
    workload
  - Make sure people blocked on your tasks know that / whether you are working
    on those tasks
  - Broadcast if you are blocked or if you don't have tasks
  - A TODO email replaces stand-up meetings
- When to send an email:
  - Within the first hour of beginning the day
    - There is no hard deadline, given that we have people working from
      different time zones. Doing it first thing in the morning ensures one
      doesn't forget
  - It is recommended to check the inbox (email, GitHub) first to reflect all
    the update in the plan for the day
- Send an email to:
  - For permanent team members/people on a 3-month trial: `eng@...`
  - For interns or collaborators: `contributors@...`
- Email subject:
  - `TODO` (all caps)
  - It makes it easier to filter emails by subject
- Reply to your previous TODO email so that at least last week of TODOs is
  included
- Specify how many hours are you going to work today
  - On Monday we also specify an estimation for a week
  - No need to be too specific, give just an approximation
- List all the tasks you're going to work during the day in priority order
  - Add a hyperlink to the corresponding GitHub issue to each task in order to
    ease the navigation <img width="381" src="https://github.com/sorrentum/sorrentum/assets/31514660/0d2fbba4-1e6c-4c39-9c04-7ffc4acdde81">
  - For each task provide an ETA
    - You always estimate the ETA yourself, based on the task's difficulty,
      priority and your workload
    - No reason to be optimistic: complex things take time to be done correctly
    - Use a date in the YYYY-MM-DD format, e.g. 2023-05-20
    - When possible, add "today", "yesterday", "tomorrow", "end of week" so that
      it's easier to parse
      - "End of week" generally means Friday, although it can be extended if you
        are planning to work on the weekend (provide the date to clarify)
      - If nothing is applicable, it's okay to just provide the date
    - If the originally set ETA has not been changed yet, omit "Original ETA"
      and "Reason for ETA update"
    - If your original ETA needs to be updated (e.g., you thought that you would
      have finished a task by yesterday, but it's taking longer), keep the older
      ETA (as "Original ETA") and add the new one (as "ETA")
- Report the PR/issue blocked
