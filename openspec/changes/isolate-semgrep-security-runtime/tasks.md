# Main release tasks

- [x] Record the owner-approved correction to virtualenv 21.14.12, python-discovery 1.6.1, and packaging 26.3.
- [ ] Independently accept the corrected 23-case mapping, including exact certifi, GitPython, PyJWT, and packaging selections.
- [ ] Retain the accepted review with a repository-relative or immutable reference.
- [ ] Commit test-authored content with all local hooks and retain native failing CI evidence.
- [ ] Freeze mappings, selected tests, ancestor conftest files, and transitive Python imports.
- [ ] Refresh the nine reviewed official Python packages and both frozen files.
- [ ] Add only the exact approved MCP advisory exception.
- [ ] Update documentation dependency declarations and lock, then execute real gem compatibility probes.
- [ ] After native RED acceptance, port the reviewed dev Ruby compatibility probe to `scripts/check_jekyll_dependencies.rb` and its CI workflow to `.github/workflows/docs-dependency-checks.yml`.
- [ ] Add the missing bundle-mapper source-distribution inclusion and synchronize version 0.55.11 with the changelog.
- [ ] Verify published runtime equality, strict module signatures, both audit lanes, and required local and CI gates.
- [ ] Complete independent final review and present the unmerged PR.
- [x] Update the internal wiki mirror and rebuild its graph through the coordinating agent.
- [ ] Archive with the native OpenSpec command only after the release change is complete.
