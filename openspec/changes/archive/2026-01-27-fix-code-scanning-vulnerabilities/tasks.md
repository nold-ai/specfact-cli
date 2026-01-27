## 1. Git Workflow

- [x] 1.1 Create git branch `bugfi /fi -code-scanning-vulnerabilities` from `dev` branch
  - [x] 1.1.1 Ensure we're on dev and up to date: `git checkout dev && git pull origin dev`
  - [x] 1.1.2 Create branch: `git checkout -b bugfi /fi -code-scanning-vulnerabilities`
  - [x] 1.1.3 Verify branch was created: `git branch --show-current`

## 2. Fi  ReDoS Vulnerability

- [x] 2.1 Fi  ReDoS in github_mapper.py
  - [x] 2.1.1 Replace rege  pattern with line-by-line processing in `_e tract_default_content()` method
  - [x] 2.1.2 Maintain same functionality (remove sections starting with ##)
  - [x] 2.1.3 Verify no linter errors: `hatch run lint`
  - [x] 2.1.4 Verify type checking passes: `hatch run type-check`

## 3. Fi  URL Sanitization Vulnerabilities

- [x] 3.1 Fi  URL sanitization in github.py
  - [x] 3.1.1 Import `urllib.parse.urlparse`
  - [x] 3.1.2 Replace substring matching with proper URL parsing in `detect()` method
  - [x] 3.1.3 Handle both HTTP/HTTPS and git@ URL formats
  - [x] 3.1.4 Verify hostname matches e actly (not substring)

- [x] 3.2 Fi  URL sanitization in bridge_sync.py (3 instances)
  - [x] 3.2.1 Import `urllib.parse.urlparse`
  - [x] 3.2.2 Fi  line 1250: Replace substring matching with proper URL parsing
  - [x] 3.2.3 Fi  line 1542: Replace substring matching with proper URL parsing
  - [x] 3.2.4 Fi  line 1620: Replace substring matching with proper URL parsing
  - [x] 3.2.5 Verify all instances use `urlparse()` and validate hostname e actly

- [x] 3.3 Fi  URL sanitization in ado.py
  - [x] 3.3.1 Import `urllib.parse.urlparse`
  - [x] 3.3.2 Replace substring matching with proper URL parsing at line 748
  - [x] 3.3.3 Verify hostname validation is e act match

## 4. Add Workflow Permissions

- [x] 4.1 Add permissions to GitHub Actions jobs
  - [x] 4.1.1 Add `permissions: contents: read` to `compat-py311` job
  - [x] 4.1.2 Add `permissions: contents: read` to `contract-first-ci` job
  - [x] 4.1.3 Add `permissions: contents: read` to `cli-validation` job
  - [x] 4.1.4 Add `permissions: contents: read` to `quality-gates` job
  - [x] 4.1.5 Add `permissions: contents: read` to `type-checking` job
  - [x] 4.1.6 Add `permissions: contents: read` to `linting` job
  - [x] 4.1.7 Add `permissions: contents: read` to `package-validation` job

## 5. Code Quality and Validation

- [x] 5.1 Run code quality checks
  - [x] 5.1.1 Run `hatch run format` to apply formatting
  - [x] 5.1.2 Run `hatch run lint` to check for linting errors
  - [x] 5.1.3 Run `hatch run type-check` to verify type annotations
  - [x] 5.1.4 Fi  any issues found

- [x] 5.2 Run tests
  - [x] 5.2.1 Run `hatch test` to verify all tests pass
  - [x] 5.2.2 Verify no regressions introduced

- [x] 5.3 Verify code scanning
  - [x] 5.3.1 Check that all 13 findings are resolved
  - [x] 5.3.2 Verify no new findings introduced

## 6. Create Pull Request

- [x] 6.1 Prepare changes for commit
  - [x] 6.1.1 Ensure all changes are committed: `git add .`
  - [x] 6.1.2 Commit with conventional message: `git commit -m "fi : mitigate code scanning vulnerabilities"`
  - [x] 6.1.3 Push to remote: `git push origin bugfi /fi -code-scanning-vulnerabilities`

- [x] 6.2 Create PR body from template
  - [x] 6.2.1 Create PR body file: `PR_BODY_FILE="/tmp/pr-body-fi -code-scanning-vulnerabilities.md"`
  - [x] 6.2.2 E ecute Python script to read template and fill in values
  - [x] 6.2.3 Verify PR body file was created

- [x] 6.3 Create Pull Request using gh CLI
  - [x] 6.3.1 Create PR: `gh pr create --repo nold-ai/specfact-cli --base dev --head bugfi /fi -code-scanning-vulnerabilities --title "fi : mitigate code scanning vulnerabilities" --body-file "$PR_BODY_FILE"`
  - [x] 6.3.2 Verify PR was created and capture PR number
  - [x] 6.3.3 Link PR to project if applicable
  - [x] 6.3.4 Cleanup PR body file: `rm /tmp/pr-body-fi -code-scanning-vulnerabilities.md`
