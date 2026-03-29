"""Tests for core/metadata_stamp.py"""

import sys
import os
import re

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core import metadata_stamp


class TestDetectLanguage:
    def test_detect_bash_shebang(self):
        code = "#!/bin/bash\necho hello"
        assert metadata_stamp._detect_language(code) == "bash"

    def test_detect_sh_shebang(self):
        code = "#!/bin/sh\necho hi"
        assert metadata_stamp._detect_language(code) == "bash"

    def test_detect_python_def(self):
        code = "def my_function():\n    pass"
        assert metadata_stamp._detect_language(code) == "python"

    def test_detect_python_import(self):
        code = "import os\nimport sys"
        assert metadata_stamp._detect_language(code) == "python"

    def test_detect_python_env_shebang(self):
        code = "#!/usr/bin/env python\nprint('hi')"
        assert metadata_stamp._detect_language(code) == "python"

    def test_detect_javascript_function(self):
        code = "function greet() {\n  return 'hello';\n}"
        assert metadata_stamp._detect_language(code) == "javascript"

    def test_detect_c(self):
        code = "#include <stdio.h>\nint main() { return 0; }"
        assert metadata_stamp._detect_language(code) == "c"

    def test_detect_rust(self):
        code = "fn main() {\n    let mut x = 5;\n}"
        assert metadata_stamp._detect_language(code) == "rust"

    def test_detect_go(self):
        code = "package main\nfunc main() {}"
        assert metadata_stamp._detect_language(code) == "go"

    def test_defaults_to_python(self):
        code = "hello world this is unknown"
        assert metadata_stamp._detect_language(code) == "python"


class TestStampCode:
    def test_stamp_adds_comment_to_python(self):
        code = "x = 1\nprint(x)"
        stamped = metadata_stamp.stamp_code(code)
        assert "FFA-v1" in stamped

    def test_stamp_preserves_original_code(self):
        code = "x = 42\nprint(x)"
        stamped = metadata_stamp.stamp_code(code)
        assert "x = 42" in stamped
        assert "print(x)" in stamped

    def test_stamp_inserts_after_shebang(self):
        code = "#!/usr/bin/env python\nprint('hi')"
        stamped = metadata_stamp.stamp_code(code)
        lines = stamped.split("\n")
        assert lines[0] == "#!/usr/bin/env python"
        assert "FFA-v1" in stamped

    def test_stamp_with_explicit_language(self):
        code = "console.log('hello');"
        stamped = metadata_stamp.stamp_code(code, language="javascript")
        assert "//" in stamped  # JS comment style
        assert "FFA-v1" in stamped

    def test_stamp_c_uses_block_comment(self):
        code = "int x = 5;"
        stamped = metadata_stamp.stamp_code(code, language="c")
        assert "/*" in stamped
        assert "FFA-v1" in stamped

    def test_short_code_not_stamped(self):
        code = "x = 1"
        assert len(code.strip()) < 10
        stamped = metadata_stamp.stamp_code(code)
        # Short code returned as-is
        assert stamped == code

    def test_empty_code_returned_as_is(self):
        assert metadata_stamp.stamp_code("") == ""

    def test_stamp_includes_timestamp(self):
        code = "def foo(): pass"
        stamped = metadata_stamp.stamp_code(code)
        # Timestamp in YYYYMMDD_HHMMSS format
        assert re.search(r"\d{8}_\d{6}", stamped)

    def test_stamp_includes_ref(self):
        code = "def foo(): pass"
        stamped = metadata_stamp.stamp_code(code)
        assert "Ref:" in stamped


class TestShouldStamp:
    def test_python_code_block(self):
        msg = "Here is the code:\n```python\nprint('hi')\n```"
        assert metadata_stamp.should_stamp(msg) is True

    def test_bash_code_block(self):
        msg = "Run this:\n```bash\necho hi\n```"
        assert metadata_stamp.should_stamp(msg) is True

    def test_def_keyword(self):
        assert metadata_stamp.should_stamp("def my_func(): pass") is True

    def test_import_keyword(self):
        assert metadata_stamp.should_stamp("import os") is True

    def test_shebang(self):
        assert metadata_stamp.should_stamp("#!/bin/bash") is True

    def test_plain_text_no_stamp(self):
        assert metadata_stamp.should_stamp("The weather today is nice.") is False

    def test_empty_string_no_stamp(self):
        assert metadata_stamp.should_stamp("") is False


class TestStampResponse:
    def test_non_code_response_unchanged(self):
        response = "The weather is nice today."
        assert metadata_stamp.stamp_response(response) == response

    def test_code_block_gets_stamped(self):
        response = "Here:\n```python\ndef foo():\n    pass\n```"
        stamped = metadata_stamp.stamp_response(response)
        assert "FFA-v1" in stamped

    def test_non_code_text_around_block_preserved(self):
        response = "Before\n```python\nprint('hi')\n```\nAfter"
        stamped = metadata_stamp.stamp_response(response)
        assert "Before" in stamped
        assert "After" in stamped


class TestSessionInfo:
    def test_get_session_id_returns_string(self):
        sid = metadata_stamp.get_session_id()
        assert isinstance(sid, str)
        assert len(sid) > 0

    def test_session_id_is_stable(self):
        assert metadata_stamp.get_session_id() == metadata_stamp.get_session_id()

    def test_get_launch_time_returns_string(self):
        lt = metadata_stamp.get_launch_time()
        assert isinstance(lt, str)
        assert len(lt) > 0
