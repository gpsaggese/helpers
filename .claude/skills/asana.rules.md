- This document contains the rules and invariants to sync project emails from Gmail
  into Asana

# Source of Truth

## Project to Asana Board Mapping

- The mapping lives in `research/contributors.md` in the repo
  `gpsaggese/gpsaggese.github.io`
  - URL: `https://github.com/gpsaggese/gpsaggese.github.io/blob/master/research/contributors.md`
  - Read the file at every run, since the links in the file change
  - Never hard-code Asana project IDs in a skill, a plan, or a script
- Each project is an H3 section under `## Projects` with a bullet
  `**Asana board**: [<TEXT>](<URL>)`
  - The section title starts with the project name
    - `Noesis` matches `### Noesis`
    - `Tymes` matches `### Tymes.ai`
    - `Tyrn` matches `### Tyrn.dev`
- `<PROJECT_GID>` is the URL segment `/project/<PROJECT_GID>/`
  - E.g., `https://app.asana.com/1/<WORKSPACE_GID>/project/<PROJECT_GID>/list/<ID>`
- A successful `get_project` is the only proof of access to a project
  - The workspace in the URL can be missing from the `workspaces` list of `get_me`
  - Do not read or write the tasks of a project without this proof

## Project Signals

- A signal links an email to a project
- The signals of a project are:
  - The links of the project section: Google doc IDs and Google Drive folder IDs,
    which appear in sharing and comment notifications
  - GitHub repo or org names
  - The project name
  - The names and emails of the people of the project
- The people of a project come from:
  - The contributors table (`Project` column), only for the projects that have
    rows in the table, e.g., `Noesis`
  - The Asana project members, for the other projects

# Gmail

## Mailbox

- The mailbox is `saggese@gmail.com`
- Read only from this mailbox, since the Gmail connector can link to another account
- If the connected mailbox is another one, stop and tell the user

## Read-Only Access

- Use only the read tools of the Gmail connector: `search_threads`, `get_thread`,
  `get_message`
- Never send, reply, forward, draft, label, archive, or trash a message

## Relevance

- Keep a message if it concerns a project:
  - Sent by or to a contributor of the project
  - Mentions the project name
  - Is a Google Docs, Drive, or GitHub notification about a project artifact
- Skip a message if it is:
  - A newsletter or marketing mail
  - An Asana notification, since the content is already in Asana
  - Unrelated to every project

# Emails in Asana

## Copy Verbatim

- Copy the email text as received, one Asana comment per message, oldest first
  - Do not summarize, translate, or reword
  - Remove only the quoted history of earlier messages (lines starting with `>` and
    the `On <DATE>, <NAME> wrote:` block), since each earlier message has its own
    comment
- Do not upload attachments
  - List the attachment names at the end of the comment

## Comment Format

- Start every comment with the marker line `[gmail:<MESSAGE_ID>]`
  - The marker makes a re-run skip the messages that are already copied
- Use this layout:
  ```text
  [gmail:<MESSAGE_ID>] Email copied from Gmail
  From: <FROM>
  To: <TO>
  Cc: <CC>
  Date: <DATE>
  Subject: <SUBJECT>
  Link: https://mail.google.com/mail/u/saggese@gmail.com/#all/<THREAD_ID>

  <BODY>

  Attachments (not copied): <NAMES>
  ```
- Omit the `Cc` and `Attachments` lines when empty
- Label the parts of a split comment `(1/2)`, `(2/2)`, with the marker on the first
  part only

# Matching Emails to Tasks

## Outcomes

- Give each message exactly one outcome:
  - **Comment**: the message belongs to an existing task
  - **New task**: the message holds an activity that no task tracks
  - **Skip**: the marker is already in the task comments, or the message is not
    relevant
  - **Decide**: two or more tasks fit, or two or more projects fit
- Do not guess on `Decide`: list the candidates in the plan and let the user choose

## Match to an Existing Task

- Compare the message with the name, description, assignee, and section of each task
  - Same deliverable or topic
  - Sender or recipient is the assignee or a project member
- Completed tasks are candidates too, since a late reply can belong to a closed task
- A strong match is a task with the same deliverable and a related person
  - E.g., an email from a contributor about the draft of a report matches the task
    "Draft report"

## Create a New Task

- Create a task only for a concrete activity in the email:
  - A request, a commitment, a deadline, a decision to execute, or a meeting to
    prepare
- Never duplicate a task that exists
  - If a similar task exists, use the outcome `Comment` on it
- Task fields:
  - **Name**: imperative phrase under 80 characters
  - **Notes**: one or two lines on what and why, plus the Gmail link
  - **Due date**: only if the email states a date explicitly
  - **Assignee**: only if the email names one project member without ambiguity,
    otherwise leave it empty
  - **Section**: the section that holds similar tasks, or the default one
- The email is the first comment of the new task, in the comment format above

## Changes to Existing Tasks

- Do not change the name, assignee, due date, or status of an existing task
- A change that an email suggests is a suggestion, not an action
  - Apply it only if the user approves it explicitly

# Plan Before Change

## Plan Content

- Write every change to Asana in a plan before it happens
- Follow the template `.claude/templates/asana_plan.template.md`
- Link every task to update with its Asana URL
  - Use the `permalink_url` field of the task when available
  - Otherwise use `https://app.asana.com/0/<PROJECT_GID>/<TASK_GID>`
- Keep the plan short
  - One bullet per action
  - Never paste an email body in the plan
- Put a suggested change to an existing task under `Suggested Field Changes`
- Put a message with outcome `Decide` under `Needs Decision`

## Approval Gate

- Do not call `add_comment`, `create_tasks`, `update_tasks`, or any other Asana
  write tool until the user approves the plan
- The user can edit the plan before approving
  - The plan at the time of approval is the only source of actions
  - Skip an item that the user deleted or left out

## Privacy

- The plan and the emails contain private student data
  - Keep the plan out of commits
  - Copy emails only to the Asana project of the matched contributor group
