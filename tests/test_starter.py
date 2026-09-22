import json

import awkward as ak
import numpy as np
import pytest
import uproot

from dimuon.cli import main
from dimuon.config import REQUIRED_BRANCHES, InspectionConfig, load_config
from dimuon.demo import create_demo
from dimuon.inspection import inspect_dataset


@pytest.fixture
def demo(tmp_path):
    return create_demo(tmp_path / "demo.root")


@pytest.mark.parametrize(
    "updates",
    [
        {"source": ""},
        {"tree": ""},
        {"entry_start": -1},
        {"entry_stop": 0},
        {"entry_stop": 100_001},
        {"entry_stop": True},
        {"entry_start": 1.5},
        {"timeout_seconds": 0},
        {"timeout_seconds": float("nan")},
        {"timeout_seconds": 121},
        {"branches": ["nMuon"]},
        {"branches": "nMuon"},
    ],
)
def test_invalid_config(updates):
    options = {"source": "fake.root", **updates}
    with pytest.raises(ValueError):
        InspectionConfig(**options)


def test_config_unknown_fields(tmp_path):
    path = tmp_path / "config.json"
    path.write_text('{"source":"fake.root","typo":1}')
    with pytest.raises(ValueError, match="Invalid configuration"):
        load_config(path)


def test_config_non_object(tmp_path):
    path = tmp_path / "config.json"
    path.write_text("[]")
    with pytest.raises(ValueError, match="JSON object"):
        load_config(path)


def test_inspection_is_bounded_and_synthetic(demo):
    result = inspect_dataset(InspectionConfig(str(demo), entry_start=1, entry_stop=4))
    assert result["entries_read"] == 3
    assert result["tree_entries_total"] == 5
    assert result["muon_multiplicity_counts"] == {"1": 1, "2": 2}
    assert result["data_kind"] == "synthetic-demo-not-physics-data"
    assert result["source_record"] is None
    assert result["sample_is_random"] is False
    assert len(result["preview_first_three_events"]) == 3
    assert result["events_with_exactly_two_muons"] == 2


def test_end_is_clipped_and_reported(demo):
    result = inspect_dataset(InspectionConfig(str(demo), entry_stop=1000))
    assert result["entries_read"] == 5
    assert result["entry_stop_effective"] == 5
    assert result["entry_stop_requested"] == 1000


def test_out_of_bounds(demo):
    with pytest.raises(ValueError, match="outside"):
        inspect_dataset(InspectionConfig(str(demo), entry_start=5, entry_stop=6))


def test_missing_tree(demo):
    with pytest.raises(ValueError, match="not found"):
        inspect_dataset(InspectionConfig(str(demo), tree="Wrong"))


def test_missing_branch(tmp_path):
    path = tmp_path / "bad.root"
    with uproot.recreate(path) as root_file:
        root_file.mktree("Events", {"nMuon": "int32"})
        root_file["Events"].extend({"nMuon": np.array([0], dtype=np.int32)})
    with pytest.raises(ValueError, match="Missing required branches"):
        inspect_dataset(InspectionConfig(str(path)))


def test_demo_refuses_overwrite(demo):
    with pytest.raises(FileExistsError):
        create_demo(demo)


def test_config_duplicate_branches():
    with pytest.raises(ValueError, match="Duplicate"):
        InspectionConfig("fake.root", branches=REQUIRED_BRANCHES + ("nMuon",))


def test_inconsistent_multiplicity(tmp_path):
    path = tmp_path / "inconsistent.root"
    schema = {"nMuon": "int32"}
    schema.update({name: "var * float64" for name in REQUIRED_BRANCHES if name != "nMuon"})
    data = {"nMuon": np.array([2], dtype=np.int32)}
    data.update({name: ak.Array([[1.0]]) for name in REQUIRED_BRANCHES if name != "nMuon"})
    with uproot.recreate(path) as root_file:
        root_file.mktree("Events", schema)
        root_file["Events"].extend(data)
    with pytest.raises(ValueError, match="disagrees with nMuon"):
        inspect_dataset(InspectionConfig(str(path)))


def test_cli_success(demo, tmp_path, capsys):
    config = tmp_path / "config.json"
    config.write_text(json.dumps({"source": str(demo)}))
    output = tmp_path / "report.json"
    assert (
        main(["inspect", "--config", str(config), "--entries", "2", "--output", str(output)]) == 0
    )
    result = json.loads(output.read_text())
    assert result["entries_read"] == 2
    assert json.loads(capsys.readouterr().out)["status"] == "ok"


def test_cli_error_is_nonzero(tmp_path, capsys):
    assert main(["inspect", "--config", str(tmp_path / "missing.json")]) == 1
    error = json.loads(capsys.readouterr().err)
    assert error["status"] == "error"
    assert error["error_type"] == "FileNotFoundError"


def test_output_refuses_overwrite(tmp_path, capsys):
    output = tmp_path / "existing.json"
    output.write_text("keep me")
    assert main(["environment", "--output", str(output)]) == 1
    assert output.read_text() == "keep me"
    assert json.loads(capsys.readouterr().err)["error_type"] == "FileExistsError"
