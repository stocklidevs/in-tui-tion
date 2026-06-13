"""Unified-diff parser (engine-free, headless)."""

from intui.kit.state import DiffLineKind, parse_unified_diff

SAMPLE = """\
--- a/src/app.py
+++ b/src/app.py
@@ -1,3 +1,4 @@
 import os
-old_line = 1
+new_line = 2
+extra = 3
 trailing = True
--- a/README.md
+++ b/README.md
@@ -1 +1 @@
-# Old
+# New
"""


def test_parses_multiple_files() -> None:
    files = parse_unified_diff(SAMPLE)
    assert [f.path for f in files] == ["src/app.py", "README.md"]


def test_counts_added_and_removed() -> None:
    files = parse_unified_diff(SAMPLE)
    app = files[0]
    assert app.added == 2  # new_line, extra
    assert app.removed == 1  # old_line


def test_line_classification() -> None:
    app = parse_unified_diff(SAMPLE)[0]
    kinds = [line.kind for line in app.lines]
    assert DiffLineKind.CONTEXT in kinds
    assert DiffLineKind.ADD in kinds
    assert DiffLineKind.REMOVE in kinds
    added = [line.text for line in app.lines if line.kind is DiffLineKind.ADD]
    assert "new_line = 2" in added


def test_hunk_line_numbers_seeded() -> None:
    app = parse_unified_diff(SAMPLE)[0]
    first_context = next(line for line in app.lines if line.kind is DiffLineKind.CONTEXT)
    assert first_context.old_no == 1
    assert first_context.new_no == 1


def test_binary_file_marked_no_text_diff() -> None:
    text = (
        "--- a/img.png\n+++ b/img.png\nBinary files a/img.png and b/img.png differ\n"
    )
    files = parse_unified_diff(text)
    assert len(files) == 1
    assert files[0].no_text_diff is True
    assert files[0].lines == ()


def test_malformed_lines_tolerated() -> None:
    text = "--- a/x\n+++ b/x\n@@ bogus hunk @@\n?weird line\n+ok\n"
    files = parse_unified_diff(text)
    assert files[0].added == 1
    # the weird line is treated as context, not a crash
    assert any(line.kind is DiffLineKind.CONTEXT for line in files[0].lines)


def test_windows_path_separators_normalized() -> None:
    text = "--- a/src\\app.py\n+++ b/src\\app.py\n@@ -1 +1 @@\n-a\n+b\n"
    files = parse_unified_diff(text)
    assert files[0].path == "src/app.py"


def test_empty_input_returns_no_files() -> None:
    assert parse_unified_diff("") == ()
