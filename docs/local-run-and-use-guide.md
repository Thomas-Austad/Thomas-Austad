# Start and use Talent Advisor on Windows

Talent Advisor is a private, single-user application that runs on your own
computer. It prepares and reviews application materials; it **does not submit
applications**. An employer-page handoff only opens a validated employer page
that you choose to complete and submit yourself.

## Start Talent Advisor

1. Double-click `scripts\Start-TalentAdvisor.vbs` in the Talent Advisor folder.
2. On the first run, choose **Yes** if you want the launcher to install its
   private local application files. The launcher never installs software
   without this confirmation.
3. Enter your OpenAI API key when prompted. It is masked while you type and is
   saved only in your private local settings. You will never need to edit a
   configuration file or copy a sign-in token.
4. Wait while Talent Advisor verifies its private local storage. When it is
   ready, your Career Workspace opens automatically in your default browser.

Keep the Talent Advisor folder in a private location on your Windows account.
The application listens only on your computer’s loopback address and never
creates a public link or tunnel.

Before the first launch, install these normal desktop prerequisites:

- Python 3.11 or later;
- Docker Desktop, with its engine running;
- Node.js LTS and pnpm; and
- an OpenAI API key that can use the configured model.

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
| An OpenAI problem occurs while creating a profile or package | Confirm that your API key is active and has access to the configured model, then restart Talent Advisor. |

Do not remove Docker volumes, the `.env` file, the local database, or the
`var/audit/` directory unless you intentionally want to permanently delete
private application data.

## Developer support path

The graphical launcher is the supported ordinary-user entry point. Developers
can find command-line setup, tests, and troubleshooting information in
[`dev-setup.md`](dev-setup.md) and [`operations-runbook.md`](operations-runbook.md).
The MCP server is a developer integration surface, not a browser application
and not a required step for personal use.
