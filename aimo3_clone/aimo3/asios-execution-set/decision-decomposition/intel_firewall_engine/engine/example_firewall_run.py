from intel_firewall_engine.engine.primitives import EntangledVariable
from intel_firewall_engine.engine.firewall import IntelligenceFirewall

signal = EntangledVariable(
    name="INTEL_SIGNAL",
    states={"SIGINT": 0.9, "HUMINT": 0.7, "OSINT": 0.5}
)

fw = IntelligenceFirewall("event_horizon", permeability=0.6)

observed = fw.observe(signal.states)
signal.states = observed
signal.normalize()

print("Post-firewall states:", signal.states)
print("Contradiction index:", fw.contradiction_index())
