# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Sergejs Sušinskis
# See LICENSE file in the repository root for full license text.

"""Input sanitization helpers for migration CLI tools."""

from __future__ import annotations

import re

# Artifact names must be lowercase alphanumeric with hyphens/underscores,
# matching the pattern already enforced for review records.
_VALID_ARTIFACT_NAME_RE = re.compile(r"^[a-z0-9][a-z0-9\-_]*$")


def validate_artifact_name(name: str) -> str:
    """Validate and return an artifact name safe for path construction.

    Rejects names containing path traversal components (``/``, ``\\``,
    ``..``, null bytes) and names that don't match the expected
    lowercase-alphanumeric-with-hyphens pattern.

    Raises ``ValueError`` for invalid names.
    """
    if not name:
        raise ValueError("Artifact name must not be empty")
    if "/" in name or "\\" in name or "\0" in name or ".." in name:
        raise ValueError(f"Invalid artifact name (path traversal): {name!r}")
    if not _VALID_ARTIFACT_NAME_RE.fullmatch(name):
        raise ValueError(
            f"Invalid artifact name (must match [a-z0-9][a-z0-9\\-_]*): {name!r}"
        )
    return name
