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

"""Subprocess sandbox for example validation.

In-process validation (docgen/validator) executes target and generated code in
the host interpreter — fine for code you trust. When the target is less trusted,
`validate_in_sandbox` runs the same check in a short-lived child process with a
timeout, so a hang or crash can't take down the host and the blast radius is one
disposable process.

ponytail: a subprocess with a timeout — not a real security boundary (no seccomp,
namespaces, or resource caps). It contains hangs and crashes, not malice. A true
sandbox (container / gVisor) is the upgrade path; this is the pragmatic first
step and enough for "I mostly trust this, but don't want a runaway import."
"""

from __future__ import annotations

import json
import subprocess
import sys

_DEFAULT_TIMEOUT = 10

# Runs in the child. Reads a JSON job from stdin, exits 0 if the example loaded
# (and, for a class seam, a concrete subclass instantiated), else non-zero.
_RUNNER = r"""
import importlib, json, sys

job = json.loads(sys.stdin.read())
sys.path.insert(0, job["root"])
try:
    namespace = {}
    exec(compile(job["code"], "<sandbox-example>", "exec"), namespace)
    if job["kind"] in ("class", "abstract_class"):
        base = getattr(importlib.import_module(job["module"]), job["symbol"])
        if not isinstance(base, type):
            sys.exit(1)
        for value in namespace.values():
            if isinstance(value, type) and value is not base:
                try:
                    if issubclass(value, base):
                        value()
                        sys.exit(0)
                except Exception:
                    pass
        sys.exit(1)
    sys.exit(0)  # non-class seam: loading clean is enough
except Exception:
    sys.exit(1)
"""


def validate_in_sandbox(
    root: str,
    module: str,
    symbol: str,
    code: str,
    kind: str,
    timeout: int = _DEFAULT_TIMEOUT,
) -> bool:
    """Validate an example in a child process. True if it loaded/instantiated."""
    job = json.dumps(
        {"root": root, "module": module, "symbol": symbol, "code": code, "kind": kind}
    )
    try:
        proc = subprocess.run(
            [sys.executable, "-c", _RUNNER],
            input=job,
            text=True,
            capture_output=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return False
    return proc.returncode == 0
