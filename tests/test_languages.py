# Copyright 2026 Rinkia
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Self-check for the language front-end registry."""

from __future__ import annotations

import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modscan.languages import (  # noqa: E402
    LanguageParser,
    available_languages,
    get_language_parser,
    register_language,
)


def test_python_is_registered() -> None:
    assert "python" in available_languages()
    parser = get_language_parser("python")
    assert isinstance(parser, LanguageParser)
    assert parser.name == "python"


def test_python_parser_still_parses() -> None:
    with tempfile.TemporaryDirectory() as root:
        with open(os.path.join(root, "m.py"), "w", encoding="utf-8") as fh:
            fh.write("def f():\n    return 1\n")
        cb = get_language_parser("python").parse_codebase(root)
        assert any(m.qualname == "m" for m in cb.modules)


def test_unknown_language_lists_available() -> None:
    try:
        get_language_parser("cobol")
    except ValueError as exc:
        assert "python" in str(exc)  # helpful: lists what's available
    else:
        raise AssertionError("expected ValueError")


def test_register_custom_language() -> None:
    class FakeLang:
        name = "fakelang"

        def parse_codebase(self, root: str):
            from modscan.models import Codebase

            return Codebase(root=root)

    register_language(FakeLang())
    assert "fakelang" in available_languages()
    assert get_language_parser("fakelang").parse_codebase(".").root == "."


if __name__ == "__main__":
    test_python_is_registered()
    test_python_parser_still_parses()
    test_unknown_language_lists_available()
    test_register_custom_language()
    print("OK: languages self-check passed")
