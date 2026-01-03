from intel_firewall_engine.engine.primitives import EntangledVariable
from intel_firewall_engine.engine.firewall import IntelligenceFirewall
from intel_firewall_engine.engine.entanglement_tracker import EntanglementTracker
from intel_firewall_engine.engine.firewall_evaporation import FirewallEvaporation

signal = EntangledVariable(
    name="INTEL_SIGNAL",
    states={"SIGINT": 0.9, "HUMINT": 0.7, "OSINT": 0.5}
)

fw = IntelligenceFirewall("event_horizon", permeability=0.6)
tracker = EntanglementTracker(coupling=0.2)
evap = FirewallEvaporation(leakage_rate=0.1)

post_fw = fw.observe(signal.states)
post_entangled = tracker.entangle(post_fw)
post_evap = evap.evaporate(post_entangled)

signal.states = post_evap
signal.normalize()

print("Final states:", signal.states)
print("Contradiction index:", fw.contradiction_index())
