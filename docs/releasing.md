# Releasing

A release is a GitHub release with the Windows EXE `EthosLogAnalyser-vX.Y.Z.exe` attached and the matching CHANGELOG section as release notes. It is built and published by GitHub Actions ([`.github/workflows/release.yml`](../.github/workflows/release.yml)) when a version tag `vX.Y.Z` is pushed. Nobody builds or uploads the EXE by hand.

## Steps

1. **Raise the version** in `src/ethosloganalyser/__init__.py` (`__version__ = "X.Y.Z"`, [semantic versioning](https://semver.org/)). Skip this if the version has not been released yet.
2. **Update `CHANGELOG.md`**: a section `## X.Y.Z` at the top that lists the user-visible changes in English. This section becomes the release notes.
3. **Open a pull request** with these changes. Besides the normal tests, the *Release* workflow runs a dry run on it: it checks version and changelog, builds the EXE and uploads it with the release notes as the artifact `release-preview`. Merge the pull request when everything is green.
4. **Set the tag** on the merged commit on `main` – only the maintainer does this:

   ```bat
   git checkout main
   git pull
   git tag vX.Y.Z
   git push origin vX.Y.Z
   ```

   Alternatively create the tag on GitHub under *Releases → Draft a new release → Choose a tag* and only create the tag there; the workflow creates the release itself, so do not publish the draft.
5. **Wait for the *Release* workflow** (Actions tab, about 10 minutes). The release then appears under [Releases](https://github.com/RollingGecko/EthosLogAnalyser/releases).

## What the workflow checks

The release is not created if any of these fail:

- the tag has the form `vX.Y.Z` and matches `__version__`,
- `CHANGELOG.md` has a non-empty section `## X.Y.Z`,
- all tests pass (same matrix as on every push: Linux with Python 3.9 and 3.12, Windows with Python 3.12),
- the EXE is built.

The same version check runs locally without installing anything:

```bat
python scripts\release_check.py --tag vX.Y.Z
```

## Dry run

*Actions → Release → Run workflow* runs everything except publishing on any branch and uploads the artifact `release-preview` (EXE and release notes). The dry run uses `__version__` and does not need a tag.

## If something went wrong

- **Check failed after the tag was pushed:** fix version or changelog in a pull request, then move the tag to the new commit: `git tag -d vX.Y.Z`, `git push origin :refs/tags/vX.Y.Z`, set the tag again (step 4).
- **Wrong release published:** delete the release and the tag on GitHub, then release a new patch version rather than reusing the number.
