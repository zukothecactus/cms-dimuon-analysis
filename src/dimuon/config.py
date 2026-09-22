"""Load and validate an explicitly bounded inspection configuration."""

import json
import math
from dataclasses import asdict, dataclass
from pathlib import Path

REQUIRED_BRANCHES = (
    "nMuon",
    "Muon_pt",
    "Muon_eta",
    "Muon_phi",
    "Muon_mass",
    "Muon_charge",
)
MAX_INSPECTION_ENTRIES = 100_000


@dataclass(frozen=True)
class InspectionConfig:
    source: str
    tree: str = "Events"
    entry_start: int = 0
    entry_stop: int = 1000
    timeout_seconds: float = 20
    branches: tuple[str, ...] = REQUIRED_BRANCHES

    def __post_init__(self):
        if not isinstance(self.source, str) or not self.source.strip():
            raise ValueError("source must be a non-empty path or URL")
        if not isinstance(self.tree, str) or not self.tree.strip():
            raise ValueError("tree must be a non-empty name")
        if type(self.entry_start) is not int or type(self.entry_stop) is not int:
            raise ValueError("entry_start and entry_stop must be integers")
        if not 0 <= self.entry_start < self.entry_stop:
            raise ValueError("Require 0 <= entry_start < entry_stop")
        if self.entry_stop - self.entry_start > MAX_INSPECTION_ENTRIES:
            raise ValueError("Day 1 inspection is capped at 100000 requested entries")
        if (
            type(self.timeout_seconds) not in (float, int)
            or not math.isfinite(self.timeout_seconds)
            or not 0 < self.timeout_seconds <= 120
        ):
            raise ValueError("timeout_seconds must be finite and in (0, 120]")
        if not isinstance(self.branches, (tuple, list)) or not self.branches:
            raise ValueError("branches must be a non-empty list")
        if any(not isinstance(branch, str) or not branch for branch in self.branches):
            raise ValueError("Every branch name must be a non-empty string")
        if len(set(self.branches)) != len(self.branches):
            raise ValueError("Duplicate branch names are not allowed")
        if not set(REQUIRED_BRANCHES).issubset(self.branches):
            raise ValueError("Configuration must include all six required muon branches")

    def to_dict(self):
        return asdict(self)


def load_config(path: str | Path) -> InspectionConfig:
    with Path(path).open(encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError("Configuration must be a JSON object")
    try:
        return InspectionConfig(**value)
    except TypeError as exc:
        raise ValueError(f"Invalid configuration fields: {exc}") from exc
