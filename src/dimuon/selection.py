import awkward as ak


def apply_baseline_selection(nMuon, Muon_charge):
    #Exactly 2 muons with opposite charges
    #Based on that create a opposite-charge mask, the 2 muons mask and the final mask
    
    #initial count
    initial_events = len(nMuon) #list of all events
    
    two_muons_mask = nMuon == 2 #creates a bool mask for nMuon
    filtered_charges = Muon_charge[two_muons_mask] #just the 2 opposite charges
    
    #filtered_charges = [[1, -1], [1, 1]]
    #   ======
    #   |1 -1|
    #   |1  1|

    events_after_two_muons = len(filtered_charges) #count of events after 2 muons selection
    
    #create a mask for opposite charges
    muon1_charge = filtered_charges[:, 0] #first muon charge (1st column) [1, 1]
    muon2_charge = filtered_charges[:, 1] #second muon charge (2nd column) [-1, 1]
    opposite_charge_mask = muon1_charge != muon2_charge #create a mask for opposite charfes
    #[True, False] #True if opposite charge, False if same charge
    #could have also checked if the sum of charges was 0 lol
    
    events_after_opposite_charge = sum(opposite_charge_mask)
    
    #just returning the counts for each cut, not the actual masks, or muons in question
    
    cutflow = {
        "initial": initial_events,
        "exactly_two_muons": int(events_after_two_muons),
        "opposite_charge": int(events_after_opposite_charge)
    } 
    
    return two_muons_mask, opposite_charge_mask, cutflow
    
def apply_pt_threshold(pt1, pt2, threshold):
    '''
        Both muons have to have transverse momentum above or at the threshold
        Returns the mask and the count of events passing the cut
    '''
    pt_mask = (pt1>=threshold) & (pt2>=threshold)
    return pt_mask, int(sum(pt_mask)) #cast to int for serialilzation