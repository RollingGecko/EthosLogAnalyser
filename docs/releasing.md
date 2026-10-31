# Releasing

A release is a GitHub release with the Windows EXE `EthosLogAnalyser-vX.Y.Z.exe` attached and the matching CHANGELOG section as release notes. It is built and published by GitHub Actions ([`.github/workflows/release.yml`](../.github/workflows/release.yml)) when a version tag `vX.Y.Z` is pushed. Nobody builds or uploads the EXE by hand.

## Steps

1. **Raise the version** in `src/ethosloganalyser/__init__.py` (`__version__ = "X.Y.Z"`, [semantic versioning](https://semver.org/); a pre-release looks like `1.0.0-beta.1`, also `-alpha.N` and `-rc.N`). Skip this if the version has not been released yet.
2. **Update `CHANGELOG.md`**: a section `## X.Y.Z` at the top that lists the user-visible changes in English. This section becomes the release notes.
3. **Open a pull request** with these changes. The *Tests* workflow checks version and changelog (job *Check version and changelog*), runs the tests and builds a test EXE for acceptance testing (see [Acceptance testing a pull request](acceptance-testing.md)). Merge the pull request when everything is green.
4. **Set the tag** on the merged commit on `main` – only the maintainer does this. Pushing the tag is what starts the release; every way below pushes an ordinary tag `vX.Y.Z` from your own account.

   *Command line:*

   ```bat
   git checkout main
   git pull
   git tag vX.Y.Z
   git push origin vX.Y.Z
   ```

   *GitHub Desktop (no command line):* switch to the branch `main` and click *Fetch origin* / *Pull origin* so that the merge commit is there. In the *History* tab, right-click the merge commit → *Create Tag…* → enter `vX.Y.Z` → *Create Tag*. Then click *Push origin*: GitHub Desktop pushes the new tag with it (the button also appears if only the tag is new).

   Do **not** create the tag on github.com under *Releases → Draft a new release*: GitHub creates a tag entered there only when the release is published, and a published release collides with the release the workflow creates.
5. **Check that the release started**: on GitHub under *Actions → Release* a run for `vX.Y.Z` must appear within a minute. If it does not, the tag was not pushed: check under *Code → Tags* and push it with the command line (step 4). Then wait for the run (about 10 minutes); the release appears under [Releases](https://github.com/RollingGecko/EthosLogAnalyser/releases).

## Pre-releases

A version with a label (`1.0.0-beta.1`) is released with the tag `v1.0.0-beta.1`; the CHANGELOG section is `## 1.0.0-beta.1`. The workflow publishes it as a GitHub *Pre-release*, so it is not shown as the latest release.

## What the workflow checks

The release is not created if any of these fail:

- the tag has the form `vX.Y.Z` (or `vX.Y.Z-beta.N`) and matches `__version__`,
- `CHANGELOG.md` has a non-empty section `## X.Y.Z`,
- all tests pass (same matrix as on every push: Linux with Python 3.9 and 3.12, Windows with Python 3.12),
- the EXE is built.

The same version check runs locally without installing anything:

```bat
python scripts\release_check.py --tag vX.Y.Z
```

## Dry run

*Actions → Release → Run workflow* runs everything except publishing on any branch and uploads the artifact `release-preview` (EXE named `EthosLogAnalyser-vX.Y.Z.exe` and the release notes). The dry run uses `__version__` and does not need a tag. Use it after changing the release pipeline itself (`release.yml`, `build.yml`, `scripts/release_check.py`, `scripts/build_exe.bat`); pull requests no longer run it automatically, so the EXE is not built twice.

## Test builds are never releases

The *Tests* workflow builds a test EXE for every pull request, every push to `main` and on demand for any branch. It shows a build tag such as `0.3.0+pr12.abc1234` and *TEST VERSION* in the app and is only available as an Actions artifact. It runs with read-only repository permissions (only the job that links the EXE in the pull request may write comments) and cannot create tags or releases. A release is published only by the *Release* workflow for a pushed tag `vX.Y.Z`, and the EXE attached to it shows the plain version.

## If something went wrong

- **Check failed after the tag was pushed:** fix version or changelog in a pull request, then move the tag to the new commit: `git tag -d vX.Y.Z`, `git push origin :refs/tags/vX.Y.Z`, set the tag again (step 4).
- **Wrong release published:** delete the release and the tag on GitHub, then release a new patch version rather than reusing the number.
