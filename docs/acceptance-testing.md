# Acceptance testing a pull request

Every change can be checked with your own logs before it is merged. For every pull request GitHub Actions builds a Windows EXE that contains the changes of the pull request. It is a **test version**, not a release: it is not attached to the releases and the app marks it clearly.

## 1. Find the test EXE

- **In the pull request:** when the checks have finished (about 10 minutes after the last commit), the bot comment *Test EXE for acceptance testing* links the download. The comment is updated after every new commit, so the link always points to the newest build.
- **Alternatively:** *Checks* tab of the pull request (or *Actions → Tests* → the run of the newest commit) → *Summary*. The artifacts are listed at the bottom of the page; the summary shows the same link.

The artifact is called `EthosLogAnalyser-<version>-pr<number>-<commit>`, for example `EthosLogAnalyser-0.3.0-pr12-abc1234`. The commit (7 characters) is the newest commit of the pull request; the EXE contains the pull request merged with the current `main`.

Pull requests from forks get no comment (they have no write access); use the run summary there.

A test EXE for any branch without a pull request: *Actions → Tests → Run workflow* → choose the branch. The artifact is then called `EthosLogAnalyser-<version>-<branch>-<commit>`.

## 2. Download and start

1. Click the artifact (you must be signed in to GitHub). The browser downloads a zip file.
2. Unpack the zip; it contains one file `EthosLogAnalyser-<version>-pr<number>-<commit>.exe`.
3. Start it. Windows SmartScreen may warn because the EXE is not signed: *More info → Run anyway*.

Artifacts are kept for 30 days. Older builds can be made again by re-running the workflow of the pull request.

## 3. Check that it is the right version

A test version shows its build tag in two places:

- **Window title:** starts with `TEST VERSION 0.3.0+pr12.abc1234 – EthosLogAnalyser` (in German `TESTVERSION …`, in Spanish `VERSIÓN DE PRUEBA …`).
- **Data & settings → About:** `EthosLogAnalyser, version 0.3.0+pr12.abc1234` and a red line *Test version (pr12.abc1234) … not a release*.

`pr12` is the number of the pull request and `abc1234` the commit; both must match the comment in the pull request. A released version shows only `0.3.0` and no red line.

## 4. Test and give feedback

- Analyse your logs as usual and go through the points under *How to review* in the pull request description.
- Compare with the last released version if the pull request changes results (keep the released EXE next to the test EXE; both can run at the same time).
- Write problems as a comment in the pull request or tell the hub.

## 5. Merge

When the test is fine and all checks are green, merge the pull request on GitHub (*Merge pull request*). Merging does **not** publish anything. A release is made later, at a time you choose, by setting a version tag (see [Releasing](releasing.md)).
