"""Fail-closed workflow contracts for bundled-module GitHub releases."""

from pathlib import Path


PUBLISH_MODULES = Path(__file__).resolve().parents[3] / ".github" / "workflows" / "publish-modules.yml"


def test_release_reuse_requires_published_exact_tag_state() -> None:
    """An interrupted draft or retargeted tag cannot advance the snapshot."""
    raw = PUBLISH_MODULES.read_text(encoding="utf-8")

    assert raw.count('gh release view "${RELEASE_TAG}" --repo "${{ github.repository }}"') >= 2
    assert raw.count("--json isDraft,publishedAt,tagName") >= 2
    assert raw.count('if [ "${IS_DRAFT}" = "true" ] || [ -z "${PUBLISHED_AT}" ]') >= 2
    assert raw.count('if [ "${PUBLISHED_TAG}" != "${RELEASE_TAG}" ]') >= 2
    assert raw.count('git fetch --force --no-tags origin "refs/tags/${RELEASE_TAG}:refs/tags/${RELEASE_TAG}"') >= 2


def test_publication_rechecks_module_cleanliness_and_uses_protected_pr_base() -> None:
    """Late untracked files and tag-shaped PR bases must fail before snapshot delivery."""
    raw = PUBLISH_MODULES.read_text(encoding="utf-8")

    assert 'git status --porcelain --untracked-files=all -- "${MODULE_PATH}"' in raw
    assert 'git status --porcelain --untracked-files=all -- "${MODULE_DIR}"' in raw
    assert 'echo "source_branch=${SOURCE_BRANCH}" >> "$GITHUB_OUTPUT"' in raw
    assert 'echo "source_branch=${HEAD_BRANCH}" >> "$GITHUB_OUTPUT"' in raw
    assert "BASE: ${{ steps.release.outputs.source_branch }}" in raw
    assert '--base "${BASE}"' in raw
    assert 'BASE="${{ github.ref_name }}"' not in raw


def test_manual_publication_allows_an_authenticated_ancestor_after_branch_advances() -> None:
    """A failed release retry remains valid after its protected branch moves."""
    raw = PUBLISH_MODULES.read_text(encoding="utf-8")

    assert 'git merge-base --is-ancestor "${SOURCE_SHA}" "origin/${SOURCE_BRANCH}"' in raw
    assert "Manual publication source is outside the selected protected branch history." in raw
    assert "Manual publication checkout does not match the protected branch tip." not in raw
