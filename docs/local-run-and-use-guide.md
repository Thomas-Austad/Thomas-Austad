# Start and use Talent Advisor on Windows

Talent Advisor is a private, single-user application that runs on your own
computer. It prepares and reviews application materials; it **does not submit
applications**. An employer-page handoff only opens a validated employer page
that you choose to complete and submit yourself.

## Start Talent Advisor

1. Double-click `scripts\Start-TalentAdvisor.cmd` in the Talent Advisor folder.
2. On the first run, choose **Yes** if you want the launcher to install its
   private local application files. The launcher never installs software
   without this confirmation.
3. Ensure Ollama is running locally with `qwen3:8b`. If the model is missing,
   the launcher names its approximate 5.2 GB download before asking whether to
   start it; you can decline and install it manually instead.
4. Wait while Talent Advisor verifies its private local storage and model. When it is
   ready, your Career Workspace opens automatically in your default browser.

Keep the Talent Advisor folder in a private location on your Windows account.
The application listens only on your computer’s loopback address and never
creates a public link or tunnel.

Before the first launch, install these normal desktop prerequisites:

- Python 3.11 or later;
- Docker Desktop, with its engine running;
- Node.js LTS and pnpm; and
- Ollama with the `qwen3:8b` model; and
- a 32 GB memory-class Windows host for the qualified local configuration.

The launcher checks each prerequisite and explains the next step in plain
language. It does not show a terminal, stack trace, database setting, or bearer
token in the ordinary user flow.

## Use the Career Workspace

1. Paste your resume, then create and review your evidence-grounded profile.
   Correct anything that is inaccurate before using it for matching.
2. Search the supported Greenhouse, Lever, or Ashby job boards and review a job
   before requesting a match or compensation estimate.
3. Prepare an application package, then review its resume, cover letter,
   warnings, and screening questions.
4. Enter and directly confirm any sensitive screening answers yourself. Talent
   Advisor does not infer legal, personal, demographic, salary-history,
   disability, criminal-history, or work-authorization answers.
5. Approve the package only when you are satisfied. **Local approval is not an
   application submission.**
6. If available, request browser handoff and then choose whether to open the
   employer page. The handoff does not transfer credentials, upload documents,
   complete a form, or report a submission.

Use **Privacy and data controls** to review retention, delete your current
local profile, or purge profiles that are due for deletion. Each destructive
action shows its exact local effect and asks for confirmation; it never affects
an employer account or application.

## Safe repeat runs and recovery

Opening the launcher again is safe. It preserves existing settings and private
database data, applies only outstanding schema updates, and opens a fresh
private browser workspace. It never offers a reset or deletes data as part of
normal startup.

| What you see | What to do |
| --- | --- |
| Docker Desktop is not ready | Start Docker Desktop, wait for its engine to report ready, then open Talent Advisor again. |
| A prerequisite is missing | Install the named desktop prerequisite, then open Talent Advisor again. The launcher will recheck it. |
| A local address is already in use | Close the other application using Talent Advisor’s private local address, then try again. If Talent Advisor is already running, opening the launcher again safely opens a fresh workspace. |
| Local storage cannot start | Confirm Docker Desktop is ready, then try again. No data is reset by a failed start. |
| The startup link expired | Close the browser tab and open Talent Advisor again from the launcher. |
| Ollama is not running or the model is missing | Start Ollama and confirm `qwen3:8b` is installed, then open Talent Advisor again. The launcher never downloads a model without first showing its size and receiving confirmation. |
| Talent Advisor cannot create a profile or package | Confirm Ollama is running locally, then try again. No profile or application is created when the local model is unavailable. |

Do not remove Docker volumes, the `.env` file, the local database, or the
`var/audit/` directory unless you intentionally want to permanently delete
private application data.

## Developer support path

The graphical launcher is the supported ordinary-user entry point. Developers
can find command-line setup, tests, and troubleshooting information in
[`dev-setup.md`](dev-setup.md) and [`operations-runbook.md`](operations-runbook.md).
The MCP server is a developer integration surface, not a browser application
and not a required step for personal use.
