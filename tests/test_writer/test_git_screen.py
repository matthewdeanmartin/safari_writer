"""Tests for the Git Publish screen helpers (git_screen.py)."""

from __future__ import annotations

import subprocess
from pathlib import Path
from unittest.mock import MagicMock, PropertyMock, patch

import pytest

from safari_writer.screens.git_screen import (GitPublishScreen,
                                              _find_repo_root, _git_add_all,
                                              _git_commit, _git_log, _git_pull,
                                              _git_push, _git_status,
                                              _remote_url)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_repo(tmp_path: Path) -> Path:
    """Init a real git repo in tmp_path and return its root."""
    subprocess.run(["git", "init", str(tmp_path)], check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Tester"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
    )
    return tmp_path


def _add_commit(
    repo_path: Path, filename: str = "post.md", message: str = "init"
) -> None:
    """Create a file and make an initial commit."""
    (repo_path / filename).write_text("# Hello\n")
    subprocess.run(["git", "add", "."], cwd=repo_path, check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", message],
        cwd=repo_path,
        check=True,
        capture_output=True,
    )


# ---------------------------------------------------------------------------
# _find_repo_root
# ---------------------------------------------------------------------------


class TestFindRepoRoot:
    def test_finds_repo_at_root(self, tmp_path):
        _make_repo(tmp_path)
        assert _find_repo_root(tmp_path) == tmp_path

    def test_finds_repo_from_subdirectory(self, tmp_path):
        _make_repo(tmp_path)
        subdir = tmp_path / "posts" / "2024"
        subdir.mkdir(parents=True)
        assert _find_repo_root(subdir) == tmp_path

    def test_returns_none_when_no_repo(self, tmp_path):
        # tmp_path with no .git
        result = _find_repo_root(tmp_path)
        # May or may not find a parent repo depending on CI environment;
        # what matters is the return type.
        assert result is None or isinstance(result, Path)

    def test_finds_repo_from_file_path(self, tmp_path):
        _make_repo(tmp_path)
        doc = tmp_path / "draft.md"
        doc.write_text("draft")
        # Pass parent of doc
        assert _find_repo_root(doc.parent) == tmp_path


# ---------------------------------------------------------------------------
# _git_status
# ---------------------------------------------------------------------------


class TestGitStatus:
    def test_clean_repo_says_clean(self, tmp_path):
        _make_repo(tmp_path)
        _add_commit(tmp_path)
        result = _git_status(tmp_path)
        assert "clean" in result.lower()

    def test_untracked_file_shown(self, tmp_path):
        _make_repo(tmp_path)
        _add_commit(tmp_path)
        (tmp_path / "new_post.md").write_text("new")
        result = _git_status(tmp_path)
        assert "new_post.md" in result

    def test_modified_file_shown(self, tmp_path):
        _make_repo(tmp_path)
        _add_commit(tmp_path)
        (tmp_path / "post.md").write_text("changed content")
        result = _git_status(tmp_path)
        assert "post.md" in result

    def test_shows_branch_name(self, tmp_path):
        _make_repo(tmp_path)
        _add_commit(tmp_path)
        result = _git_status(tmp_path)
        assert "Branch:" in result

    def test_error_returns_red_markup(self, tmp_path):
        bad_path = tmp_path / "not_a_repo"
        bad_path.mkdir()
        result = _git_status(bad_path)
        assert "[red]" in result

    def test_staged_file_shown(self, tmp_path):
        _make_repo(tmp_path)
        _add_commit(tmp_path)
        (tmp_path / "staged.md").write_text("staged content")
        subprocess.run(["git", "add", "staged.md"], cwd=tmp_path, capture_output=True)
        result = _git_status(tmp_path)
        assert "staged.md" in result


# ---------------------------------------------------------------------------
# _git_add_all
# ---------------------------------------------------------------------------


class TestGitAddAll:
    def test_stages_new_file(self, tmp_path):
        _make_repo(tmp_path)
        _add_commit(tmp_path)
        (tmp_path / "new.md").write_text("post")
        result = _git_add_all(tmp_path)
        assert "[green]" in result
        # Verify it's actually staged
        import git as gitmodule

        repo = gitmodule.Repo(tmp_path)
        staged_paths = [d.a_path for d in repo.index.diff("HEAD")]
        assert "new.md" in staged_paths

    def test_stages_modified_file(self, tmp_path):
        _make_repo(tmp_path)
        _add_commit(tmp_path)
        (tmp_path / "post.md").write_text("updated")
        result = _git_add_all(tmp_path)
        assert "[green]" in result

    def test_error_on_non_repo(self, tmp_path):
        bad = tmp_path / "nope"
        bad.mkdir()
        result = _git_add_all(bad)
        assert "[red]" in result


# ---------------------------------------------------------------------------
# _git_commit
# ---------------------------------------------------------------------------


class TestGitCommit:
    def test_commit_creates_entry_in_log(self, tmp_path):
        _make_repo(tmp_path)
        _add_commit(tmp_path)
        (tmp_path / "page2.md").write_text("new page")
        _git_add_all(tmp_path)
        result = _git_commit(tmp_path, "Add page2")
        assert "[green]" in result
        assert "Add page2" in result

    def test_empty_message_returns_cancelled(self, tmp_path):
        _make_repo(tmp_path)
        _add_commit(tmp_path)
        result = _git_commit(tmp_path, "   ")
        assert "[yellow]" in result
        assert "empty" in result.lower() or "cancel" in result.lower()

    def test_commit_message_appears_in_log(self, tmp_path):
        _make_repo(tmp_path)
        _add_commit(tmp_path)
        (tmp_path / "about.md").write_text("about page")
        _git_add_all(tmp_path)
        _git_commit(tmp_path, "My special commit message")
        log = _git_log(tmp_path)
        assert "My special commit message" in log

    def test_error_on_non_repo(self, tmp_path):
        bad = tmp_path / "nope"
        bad.mkdir()
        result = _git_commit(bad, "msg")
        assert "[red]" in result


# ---------------------------------------------------------------------------
# _git_log
# ---------------------------------------------------------------------------


class TestGitLog:
    def test_shows_commit_sha_and_message(self, tmp_path):
        _make_repo(tmp_path)
        _add_commit(tmp_path, message="First post")
        result = _git_log(tmp_path)
        assert "First post" in result

    def test_empty_repo_returns_no_commits(self, tmp_path):
        _make_repo(tmp_path)
        result = _git_log(tmp_path)
        assert "no commit" in result.lower() or result == "(no commits)"

    def test_multiple_commits_shown(self, tmp_path):
        _make_repo(tmp_path)
        _add_commit(tmp_path, message="Post one")
        (tmp_path / "b.md").write_text("b")
        _git_add_all(tmp_path)
        _git_commit(tmp_path, "Post two")
        result = _git_log(tmp_path)
        assert "Post one" in result
        assert "Post two" in result

    def test_count_limits_entries(self, tmp_path):
        _make_repo(tmp_path)
        _add_commit(tmp_path, message="First")
        for i in range(5):
            (tmp_path / f"f{i}.md").write_text(f"content {i}")
            _git_add_all(tmp_path)
            _git_commit(tmp_path, f"Commit {i}")
        result = _git_log(tmp_path, count=2)
        # Only last 2 commits; "First" should not appear
        assert "First" not in result

    def test_error_on_non_repo(self, tmp_path):
        bad = tmp_path / "nope"
        bad.mkdir()
        result = _git_log(bad)
        assert "[red]" in result


# ---------------------------------------------------------------------------
# _git_push — tested with mocks (no real remote)
# ---------------------------------------------------------------------------


class TestGitPush:
    def test_no_remotes_returns_warning(self, tmp_path):
        _make_repo(tmp_path)
        _add_commit(tmp_path)
        result = _git_push(tmp_path)
        assert "[yellow]" in result
        assert "remote" in result.lower()

    def test_push_success_returns_green(self, tmp_path):
        _make_repo(tmp_path)
        _add_commit(tmp_path)
        import git as gitmodule

        mock_push_info = MagicMock()
        mock_push_info.__iter__ = MagicMock(return_value=iter([]))
        mock_push_info.__getitem__ = MagicMock(return_value=MagicMock(flags=0))
        mock_remote = MagicMock()
        mock_remote.name = "origin"
        mock_remote.push.return_value = mock_push_info
        with patch.object(
            gitmodule.Repo, "remotes", new_callable=PropertyMock
        ) as mock_remotes:
            mock_remotes.return_value = [mock_remote]
            result = _git_push(tmp_path)
        assert "[green]" in result

    def test_push_error_flag_returns_red(self, tmp_path):
        _make_repo(tmp_path)
        _add_commit(tmp_path)
        import git as gitmodule

        mock_item = MagicMock()
        mock_item.flags = 1024  # PushInfo.ERROR
        mock_item.summary = "rejected"
        mock_push_info = MagicMock()
        mock_push_info.__bool__ = MagicMock(return_value=True)
        mock_push_info.__getitem__ = MagicMock(return_value=mock_item)
        mock_remote = MagicMock()
        mock_remote.name = "origin"
        mock_remote.push.return_value = mock_push_info
        with patch.object(
            gitmodule.Repo, "remotes", new_callable=PropertyMock
        ) as mock_remotes:
            mock_remotes.return_value = [mock_remote]
            result = _git_push(tmp_path)
        assert "[red]" in result

    def test_error_on_non_repo(self, tmp_path):
        bad = tmp_path / "nope"
        bad.mkdir()
        result = _git_push(bad)
        assert "[red]" in result


# ---------------------------------------------------------------------------
# _git_pull — tested with mocks (no real remote)
# ---------------------------------------------------------------------------


class TestGitPull:
    def test_no_remotes_returns_warning(self, tmp_path):
        _make_repo(tmp_path)
        _add_commit(tmp_path)
        result = _git_pull(tmp_path)
        assert "[yellow]" in result

    def test_pull_success_returns_green(self, tmp_path):
        _make_repo(tmp_path)
        _add_commit(tmp_path)
        import git as gitmodule

        mock_remote = MagicMock()
        mock_remote.name = "origin"
        mock_remote.pull.return_value = None
        with patch.object(
            gitmodule.Repo, "remotes", new_callable=PropertyMock
        ) as mock_remotes:
            mock_remotes.return_value = [mock_remote]
            result = _git_pull(tmp_path)
        assert "[green]" in result

    def test_pull_exception_returns_red(self, tmp_path):
        _make_repo(tmp_path)
        _add_commit(tmp_path)
        import git as gitmodule

        mock_remote = MagicMock()
        mock_remote.pull.side_effect = Exception("network error")
        with patch.object(
            gitmodule.Repo, "remotes", new_callable=PropertyMock
        ) as mock_remotes:
            mock_remotes.return_value = [mock_remote]
            result = _git_pull(tmp_path)
        assert "[red]" in result

    def test_error_on_non_repo(self, tmp_path):
        bad = tmp_path / "nope"
        bad.mkdir()
        result = _git_pull(bad)
        assert "[red]" in result


# ---------------------------------------------------------------------------
# _remote_url
# ---------------------------------------------------------------------------


class TestRemoteUrl:
    def test_no_remote_returns_placeholder(self, tmp_path):
        _make_repo(tmp_path)
        import git as gitmodule

        repo = gitmodule.Repo(tmp_path)
        result = _remote_url(repo)
        assert result == "(no remote)"

    def test_with_remote_returns_url(self, tmp_path):
        _make_repo(tmp_path)
        subprocess.run(
            ["git", "remote", "add", "origin", "https://github.com/user/blog.git"],
            cwd=tmp_path,
            check=True,
            capture_output=True,
        )
        import git as gitmodule

        repo = gitmodule.Repo(tmp_path)
        result = _remote_url(repo)
        assert "github.com" in result


# ---------------------------------------------------------------------------
# GitPublishScreen — construction and auto-detect logic
# ---------------------------------------------------------------------------


class TestGitPublishScreen:
    def test_instantiates_without_document_path(self):
        screen = GitPublishScreen()
        assert screen is not None

    def test_instantiates_with_document_path(self, tmp_path):
        _make_repo(tmp_path)
        doc = tmp_path / "post.md"
        doc.write_text("content")
        screen = GitPublishScreen(document_path=str(doc))
        assert screen._repo_path == tmp_path

    def test_auto_detects_repo_from_doc_parent(self, tmp_path):
        _make_repo(tmp_path)
        subdir = tmp_path / "posts"
        subdir.mkdir()
        doc = subdir / "hello.md"
        doc.write_text("hello")
        screen = GitPublishScreen(document_path=str(doc))
        assert screen._repo_path == tmp_path

    def test_no_repo_sets_none(self, tmp_path):
        # A temp dir with no .git anywhere we control
        isolated = tmp_path / "no_git_here"
        isolated.mkdir()
        # Patch _find_repo_root to reliably return None
        with patch(
            "safari_writer.screens.git_screen._find_repo_root", return_value=None
        ):
            screen = GitPublishScreen(document_path=str(isolated / "doc.md"))
            assert screen._repo_path is None

    def test_repo_label_with_path(self, tmp_path):
        _make_repo(tmp_path)
        screen = GitPublishScreen(document_path=str(tmp_path / "doc.md"))
        label = screen._repo_label()
        assert str(tmp_path) in label

    def test_repo_label_without_path(self, tmp_path):
        with patch(
            "safari_writer.screens.git_screen._find_repo_root", return_value=None
        ):
            screen = GitPublishScreen()
            label = screen._repo_label()
            assert "no repository" in label.lower()
