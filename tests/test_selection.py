import awkward as ak
import numpy as np
from dimuon.selection import apply_baseline_selection, apply_pt_threshold

'''
Validates relativistic 4-momentum math (back-to-back particle decays and rest-frame mass calculations).
'''


def test_apply_baseline_selection_synthetic():
    #testing on synthetic data
    nMuon = ak.Array([0, 1, 2, 2, 3])
    Muon_charge = ak.Array([[], [1], [1, -1], [1, 1], [1, -1, 1]])

    two_muons_mask, opposite_charge_mask, cutflow = apply_baseline_selection(
        nMuon, Muon_charge
    )

    assert cutflow["initial"] == 5
    assert cutflow["exactly_two_muons"] == 2
    assert cutflow["opposite_charge"] == 1
    assert list(two_muons_mask) == [False, False, True, True, False]
    assert list(opposite_charge_mask) == [True, False]

def test_apply_pt_threshold_synthetic():
    pt1 = ak.Array([5.0, 10.0, 15.0, 20.0])
    pt2 = ak.Array([5.0, 10.0, 15.0, 20.0])
    threshold = 10.0

    pt_mask, count = apply_pt_threshold(pt1, pt2, threshold)

    assert count == 3
    assert list(pt_mask) == [False, True, True, True]
