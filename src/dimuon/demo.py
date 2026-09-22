"""Generate five deliberately artificial events for offline plumbing tests."""

from pathlib import Path

import awkward as ak
import numpy as np
import uproot


def create_demo(path: str | Path) -> Path:
    destination = Path(path)
    if destination.exists():
        raise FileExistsError(f"Refusing to overwrite {destination}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    counts = [0, 1, 2, 2, 3]
    data = {
        "nMuon": np.array(counts, dtype=np.int32),
        "Muon_pt": ak.Array([[], [12.0], [25.0, 30.0], [15.0, 18.0], [5.0, 8.0, 11.0]]),
        "Muon_eta": ak.Array([[], [0.1], [0.2, -0.2], [0.3, -0.3], [0.0, 0.1, -0.1]]),
        "Muon_phi": ak.Array([[], [0.0], [0.0, 3.0], [1.0, -1.0], [0.0, 1.0, 2.0]]),
        # 0.1 is an arbitrary fixture mass, NOT a quoted precision muon mass.
        "Muon_mass": ak.Array([[0.1] * n for n in counts]),
        "Muon_charge": ak.Array([[], [1], [1, -1], [1, 1], [1, -1, 1]]),
    }
    schema = {"nMuon": "int32"}
    schema.update({name: "var * float64" for name in data if name.startswith("Muon_")})
    schema["Muon_charge"] = "var * int32"
    with uproot.recreate(destination) as root_file:
        root_file["starter_data_kind"] = "synthetic-demo-not-physics-data"
        root_file.mktree("Events", schema)
        root_file["Events"].extend(data)
    return destination
