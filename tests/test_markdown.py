from aiactguard.core.markdown import MarkdownReport


def test_builder_produces_expected_structure():
    report = (
        MarkdownReport("Test Report")
        .note("This is a disclaimer.")
        .heading("Section One")
        .field("Name", "value")
        .bullet("a plain bullet")
        .sub_bullet("a nested bullet")
        .build()
    )

    assert report.startswith("# Test Report\n")
    assert "> This is a disclaimer." in report
    assert "## Section One" in report
    assert "- **Name:** value" in report
    assert "- a plain bullet" in report
    assert "  - a nested bullet" in report


def test_blank_and_line_control_spacing():
    report = MarkdownReport("T").line("first").blank().line("second").build()
    assert report.split("\n")[-3:] == ["first", "", "second"]
