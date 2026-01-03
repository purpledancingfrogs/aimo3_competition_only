from mpmath import mp, zetazero
import json, hashlib

mp.dps = 80

agent = 36
t0 = (agent - 1) * 2000000
t1 = agent * 2000000

zeros = []
n = t0
while True:
    try:
        z = zetazero(n)
        im = mp.im(z)
        if im > t1:
            break
        if im >= t0:
            zeros.append(str(z))
        n += 1
    except Exception:
        break

payload = {
    "agent": agent,
    "t_start": t0,
    "t_end": t1,
    "zero_count": len(zeros),
    "zeros": zeros
}

raw = json.dumps(payload, sort_keys=True).encode()
payload["sha256"] = hashlib.sha256(raw).hexdigest()

with open("zeros_agent_%02d.json" % agent, "w") as f:
    json.dump(payload, f, indent=2)
