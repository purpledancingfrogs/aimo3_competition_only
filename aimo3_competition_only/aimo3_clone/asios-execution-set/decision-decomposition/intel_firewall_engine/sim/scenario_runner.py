from intel_firewall_engine.engine.firewalls import Firewall
from intel_firewall_engine.engine.evaporation import EvaporationModel
from intel_firewall_engine.metrics.entropy import entropy

def run_scenario(signal, firewall_opacity, half_life, dt):
    fw = Firewall("event_horizon", firewall_opacity)
    evap = EvaporationModel(half_life)

    after_fw = fw.transmit(signal)
    after_evap = {k: evap.decay(v, dt) for k, v in after_fw.items()}

    return {
        "post_firewall": after_fw,
        "post_evaporation": after_evap,
        "entropy": entropy(after_evap)
    }
