from intel_firewall_engine.engine.primitives import EntangledVariable

signal = EntangledVariable(
    name="INTEL_SIGNAL",
    states={
        "SIGINT": 0.9,
        "HUMINT": 0.7,
        "OSINT": 0.5
    }
)

signal.observe("SIGINT")
print(signal.states)
