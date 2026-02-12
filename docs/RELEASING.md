# Releasing Forbin

## Prerequisites

- Push access to this repository
- `HOMEBREW_TAP_TOKEN` secret configured in GitHub repo settings (fine-grained PAT with Contents read/write on `chris-colinsky/homebrew-forbin`)

## Release Steps

1. **Bump the version** in `pyproject.toml`:
   ```toml
   version = "0.2.0"
   ```

2. **Commit and push** to `main` (or merge a release branch):
   ```bash
   git add pyproject.toml
   git commit -m "Bump version to 0.2.0"
   git push origin main
   ```

3. **Create and push a tag**:
   ```bash
   git tag v0.2.0
   git push origin v0.2.0
   ```

   The tag must match the pattern `v*.*.*` to trigger the release workflow.

4. **The GitHub Actions workflow handles the rest**:
   - Runs tests (`uv run pytest`)
   - Builds the package
   - Publishes to PyPI as `forbin-mcp`
   - Creates a GitHub Release with auto-generated notes
   - Updates the Homebrew tap (`chris-colinsky/homebrew-forbin`)

## Verifying the Release

- **PyPI**: https://pypi.org/project/forbin-mcp/
- **GitHub Release**: Check the Releases tab on the repo
- **Homebrew**: `brew update && brew upgrade forbin`

## Versioning

This project uses semantic versioning:

- **Patch** (0.1.x): Bug fixes, minor improvements
- **Minor** (0.x.0): New features, non-breaking changes
- **Major** (x.0.0): Breaking changes

## Troubleshooting

### Workflow not triggered
Ensure the tag matches the pattern `v[0-9]*.[0-9]*.[0-9]*` and was pushed to the remote.

### PyPI publish fails
Check that the `pypi` environment is configured in repo settings with trusted publisher (PyPA).

### Homebrew update fails
- Verify the `HOMEBREW_TAP_TOKEN` secret is set and not expired
- The token needs Contents read/write permission on `chris-colinsky/homebrew-forbin`
- The workflow waits 30 seconds for PyPI to index before fetching package info; if PyPI is slow, re-run the job
