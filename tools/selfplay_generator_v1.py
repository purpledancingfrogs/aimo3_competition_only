# tools/selfplay_generator_v1.py
# Deterministic synthetic set builder (no LLM). Generates diverse olympiad-style prompts + exact integer answers.
from __future__ import annotations
import random, math, itertools, json
from dataclasses import dataclass

SEED = 1337
rng = random.Random(SEED)

@dataclass
class Item:
    prompt: str
    answer: int
    tag: str

def egcd(a,b):
    if b==0: return (a,1,0)
    g,x,y = egcd(b, a%b)
    return (g, y, x-(a//b)*y)

def crt_pair(a1,m1,a2,m2):
    g,x,y = egcd(m1,m2)
    if (a2-a1)%g!=0: return None
    l = m1//g*m2
    k = ((a2-a1)//g * x)%(m2//g)
    a = (a1 + k*m1) % l
    return (a,l)

def gen_linear():
    a = rng.randint(2,25); x = rng.randint(-200,200); b = rng.randint(-300,300)
    c = a*x + b
    p = f"Solve for x: {a}*x + {b} = {c}. Return integer only."
    return Item(p, x, "linear")

def gen_two_eq_sum():
    x = rng.randint(-50,50); y = rng.randint(-50,50)
    a1,b1 = rng.randint(1,9), rng.randint(1,9)
    a2,b2 = rng.randint(1,9), rng.randint(1,9)
    c1 = a1*x + b1*y
    c2 = a2*x + b2*y
    p = "Solve the system and return x+y as an integer only:\n" + \
        f"{a1}*x + {b1}*y = {c1}\n{a2}*x + {b2}*y = {c2}"
    return Item(p, x+y, "system_sum")

def gen_mod_pow():
    a = rng.randint(2,200); b = rng.randint(2,500); m = rng.randint(2,200)
    ans = pow(a,b,m)
    p = f"Compute {a}^{b} mod {m}. Return integer only."
    return Item(p, ans, "powmod")

def gen_crt():
    # two congruences with coprime-ish mod
    m1 = rng.randint(5,50); m2 = rng.randint(5,50)
    while math.gcd(m1,m2) != 1:
        m2 = rng.randint(5,50)
    a = rng.randint(0,m1-1); b = rng.randint(0,m2-1)
    sol = crt_pair(a,m1,b,m2)[0]
    p = f"Find the smallest nonnegative integer x satisfying: x ≡ {a} (mod {m1}) and x ≡ {b} (mod {m2})."
    return Item(p, sol, "crt")

def gen_fact_digitsum():
    n = rng.randint(5,200)
    f = math.factorial(n)
    ans = sum(int(ch) for ch in str(f))
    p = f"Find the sum of digits of {n}!. Return integer only."
    return Item(p, ans, "fact_digitsum")

def gen_nCk():
    n = rng.randint(20,400); k = rng.randint(0,min(20,n))
    ans = math.comb(n,k)
    p = f"Compute C({n},{k}). Return integer only."
    return Item(p, ans, "nCk")

def gen_gcd_lcm():
    a = rng.randint(1,10**6); b = rng.randint(1,10**6)
    g = math.gcd(a,b); l = abs(a//g*b) if g else 0
    if rng.random() < 0.5:
        return Item(f"Compute gcd({a},{b}). Return integer only.", g, "gcd")
    return Item(f"Compute lcm({a},{b}). Return integer only.", l, "lcm")

GENS = [gen_linear, gen_two_eq_sum, gen_mod_pow, gen_crt, gen_fact_digitsum, gen_nCk, gen_gcd_lcm]

def main():
    out = []
    for i in range(320):
        it = rng.choice(GENS)()
        out.append({"id": i, "tag": it.tag, "prompt": it.prompt, "answer": int(it.answer)})
    with open("tools/selfplay_v1.jsonl","w",encoding="utf-8") as f:
        for r in out:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print("WROTE tools/selfplay_v1.jsonl", len(out))

if __name__ == "__main__":
    main()
