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
    assert 'BASE="${{ steps.release.outputs.source_branch }}"' in raw
    assert 'BASE="${{ github.ref_name }}"' not in raw
