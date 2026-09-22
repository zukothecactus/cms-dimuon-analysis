"""Read a bounded sample, checking schema without selecting physics events."""

import platform
from datetime import datetime, timezone
from importlib.metadata import PackageNotFoundError, version

import awkward as ak
import numpy as np
import uproot

from dimuon.config import InspectionConfig

CMS_SOURCE = (
    "root://eospublic.cern.ch//eos/opendata/cms/derived-data/"
    "AOD2NanoAODOutreachTool/Run2012BC_DoubleMuParked_Muons.root"
)
CMS_RECORD = "https://opendata.cern.ch/record/12342"


def environment_info() -> dict:
    packages = {}
    for name in (
        "cms-dimuon-starter",
        "uproot",
        "awkward",
        "numpy",
        "fsspec",
        "fsspec-xrootd",
        "xrootd",
    ):
        try:
            packages[name] = version(name)
        except PackageNotFoundError:
            packages[name] = "not installed"
    return {
        "python": platform.python_version(),
        "platform": platform.platform(),
        "packages": packages,
    }


def inspect_dataset(config: InspectionConfig) -> dict:
    # No unrestricted tree.arrays(): only explicit branches and entry bounds.
    with uproot.open(config.source, timeout=config.timeout_seconds) as root_file:
        if config.tree not in root_file:
            raise ValueError(f"Tree {config.tree!r} not found; available keys: {root_file.keys()}")
        tree = root_file[config.tree]
        if not hasattr(tree, "num_entries") or not hasattr(tree, "arrays"):
            raise ValueError(f"Object {config.tree!r} is not an inspectable event tree")
        missing = sorted(set(config.branches) - set(tree.keys()))
        if missing:
            raise ValueError(f"Missing required branches: {', '.join(missing)}")
        total = int(tree.num_entries)
        if config.entry_start >= total:
            raise ValueError(
                f"entry_start={config.entry_start} is outside a tree of {total} entries"
            )
        stop = min(config.entry_stop, total)
        arrays = tree.arrays(
            list(config.branches),
            entry_start=config.entry_start,
            entry_stop=stop,
            library="ak",
        )
        data_kind = "unverified-input"
        if "starter_data_kind" in root_file:
            data_kind = str(root_file["starter_data_kind"])
        elif config.source == CMS_SOURCE:
            data_kind = "real-CMS-open-data"

        # Multiplicity should agree with every per-muon array, not just Muon_pt.
        for name in config.branches:
            if name.startswith("Muon_"):
                if not bool(ak.all(ak.num(arrays[name], axis=1) == arrays["nMuon"])):
                    raise ValueError(f"Per-event length of {name} disagrees with nMuon")
        multiplicities, counts = np.unique(ak.to_numpy(arrays["nMuon"]), return_counts=True)
        result = {
            "status": "ok",
            "data_kind": data_kind,
            "created_utc": datetime.now(timezone.utc).isoformat(),
            "configuration": config.to_dict(),
            "source_record": CMS_RECORD if data_kind == "real-CMS-open-data" else None,
            "tree_entries_total": total,
            "entry_start": config.entry_start,
            "entry_stop_requested": config.entry_stop,
            "entry_stop_effective": stop,
            "entries_read": len(arrays),
            "sample_is_random": False,
            "branch_types": {name: str(ak.type(arrays[name])) for name in config.branches},
            "muon_multiplicity_counts": {
                str(int(value)): int(count)
                for value, count in zip(multiplicities, counts, strict=True)
            },
            "preview_first_three_events": ak.to_list(arrays[:3]),
            "environment": environment_info(),
            "note": "Inspection only: no physics cuts, mass reconstruction, or spectrum produced.",
            "events_with_exactly_two_muons": int(np.sum(ak.to_numpy(arrays["nMuon"]) == 2)),
        }
    return result
