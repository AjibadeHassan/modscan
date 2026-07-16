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

"""Self-check for the on-disk provider cache."""

from __future__ import annotations

import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modscan.providers import CachingProvider  # noqa: E402


class _CountingProvider:
    def __init__(self, model: str = "m") -> None:
        self.model = model
        self.calls = 0

    def generate(self, system: str, prompt: str) -> str:
        self.calls += 1
        return f"answer:{prompt}"


def test_cache_hits_avoid_inner_calls() -> None:
    with tempfile.TemporaryDirectory() as d:
        inner = _CountingProvider()
        cached = CachingProvider(inner, d)

        assert cached.generate("sys", "p1") == "answer:p1"
        assert cached.generate("sys", "p1") == "answer:p1"  # served from disk
        assert inner.calls == 1  # inner hit only once

        # a different prompt is a distinct key
        cached.generate("sys", "p2")
        assert inner.calls == 2


def test_cache_persists_across_instances() -> None:
    with tempfile.TemporaryDirectory() as d:
        first = _CountingProvider()
        CachingProvider(first, d).generate("s", "hello")
        assert first.calls == 1

        # a fresh provider + cache over the same dir reuses the stored answer
        second = _CountingProvider()
        assert CachingProvider(second, d).generate("s", "hello") == "answer:hello"
        assert second.calls == 0


def test_cache_key_includes_model() -> None:
    with tempfile.TemporaryDirectory() as d:
        a = _CountingProvider(model="model-a")
        b = _CountingProvider(model="model-b")
        CachingProvider(a, d).generate("s", "p")
        # same prompt, different model -> different key -> inner is called
        CachingProvider(b, d).generate("s", "p")
        assert a.calls == 1
        assert b.calls == 1


if __name__ == "__main__":
    test_cache_hits_avoid_inner_calls()
    test_cache_persists_across_instances()
    test_cache_key_includes_model()
    print("OK: cache self-check passed")
