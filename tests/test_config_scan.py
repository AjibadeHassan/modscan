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

"""Self-check for config / data-driven extension surface detection."""

from __future__ import annotations

import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modscan.config_scan import find_config_points, render_config_markdown  # noqa: E402
from modscan.cli import main  # noqa: E402


def _make_tree(root: str) -> None:
    os.makedirs(os.path.join(root, "mods"))
    os.makedirs(os.path.join(root, "src"))
    open(os.path.join(root, "plugins.json"), "w").close()
    open(os.path.join(root, "config.yaml"), "w").close()
    open(os.path.join(root, "src", "main.py"), "w").close()  # not a config surface
    open(os.path.join(root, "README.md"), "w").close()  # not a config surface


def test_finds_manifests_and_dirs() -> None:
    with tempfile.TemporaryDirectory() as root:
        _make_tree(root)
        points = find_config_points(root)
        by_path = {p.path: p for p in points}

        assert by_path["plugins.json"].kind == "manifest_file"
        assert by_path["config.yaml"].kind == "manifest_file"
        assert by_path["mods"].kind == "data_dir"
        # ordinary source / docs are not flagged
        assert "src/main.py" not in by_path
        assert "README.md" not in by_path


def test_empty_tree_reports_none() -> None:
    with tempfile.TemporaryDirectory() as root:
        os.makedirs(os.path.join(root, "src"))
        open(os.path.join(root, "src", "a.py"), "w").close()
        assert find_config_points(root) == []
        assert "None found" in render_config_markdown([])


def test_cli_config_subcommand() -> None:
    with tempfile.TemporaryDirectory() as root:
        _make_tree(root)
        assert main(["config", root]) == 0
        assert main(["config", os.path.join(root, "does-not-exist")]) == 2


if __name__ == "__main__":
    test_finds_manifests_and_dirs()
    test_empty_tree_reports_none()
    test_cli_config_subcommand()
    print("OK: config_scan self-check passed")
