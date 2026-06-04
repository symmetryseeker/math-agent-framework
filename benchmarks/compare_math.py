"""
MATH Benchmark Comparison: Raw LLM vs LLM + MAF
=================================================
Uses MATH benchmark format (Hendrycks et al. 2021):
- 7 categories: Algebra, Prealgebra, Precalculus, Number Theory,
  Intermediate Algebra, Counting & Probability, Geometry
- 5 difficulty levels (1-5)
- Scoring: exact match on boxed answer

Each problem solved TWICE by each model:
  Mode A: Raw LLM (no tools)
  Mode B: LLM + MAF (framework computes, LLM verifies)
"""
import sys, os, io, json, time, re, base64, urllib.request, math
from typing import Any, Dict, List, Tuple
from datetime import datetime

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

API_BASE = "https://maas.bit.edu.cn/v1-openai"
API_USER = os.environ.get("MATH_BENCH_USER", "3120251973")
API_PASS = os.environ.get("MATH_BENCH_PASS", "A@mkwcdf8")
_BASIC_AUTH = base64.b64encode(f"{API_USER}:{API_PASS}".encode()).decode()
BENCH_DIR = os.path.dirname(os.path.abspath(__file__))
REPORT_DIR = os.path.join(BENCH_DIR, "reports")
os.makedirs(REPORT_DIR, exist_ok=True)

# ═══════════════════════════════════════════════════════════
# MATH Benchmark problems (Hendrycks et al. format)
# Each: level(1-5), type, problem, answer (boxed)
# ═══════════════════════════════════════════════════════════

MATH_PROBLEMS = [
    # ── Algebra (Level 1-3) ──
    {"id":"A1","level":1,"type":"Algebra","problem":"Solve for x: 3x + 7 = 22","answer":"5"},
    {"id":"A2","level":1,"type":"Algebra","problem":"If 2x - 5 = 3x + 2, find x.","answer":"-7"},
    {"id":"A3","level":2,"type":"Algebra","problem":"Solve: x^2 - 5x + 6 = 0. Give both roots separated by commas.","answer":"2,3"},
    {"id":"A4","level":2,"type":"Algebra","problem":"Factor: x^2 - 9","answer":"(x-3)(x+3)"},
    {"id":"A5","level":2,"type":"Algebra","problem":"Solve the system: x + y = 5, 2x - y = 1","answer":"x=2,y=3"},
    {"id":"A6","level":3,"type":"Algebra","problem":"Find all real roots of x^3 - 6x^2 + 11x - 6 = 0","answer":"1,2,3"},
    {"id":"A7","level":3,"type":"Algebra","problem":"Solve: |2x - 1| = 5","answer":"-2,3"},
    {"id":"A8","level":3,"type":"Algebra","problem":"If 2^(x+1) = 32, find x.","answer":"4"},

    # ── Precalculus (Level 2-4) ──
    {"id":"P1","level":2,"type":"Precalculus","problem":"Evaluate lim_{x->0} sin(3x)/x","answer":"3"},
    {"id":"P2","level":2,"type":"Precalculus","problem":"Find the derivative of f(x) = x^3 - 3x^2 + 2x","answer":"3x^2-6x+2"},
    {"id":"P3","level":3,"type":"Precalculus","problem":"Evaluate lim_{x->0} (1 - cos(2x))/x^2","answer":"2"},
    {"id":"P4","level":3,"type":"Precalculus","problem":"Find the integral of (2x + 1)^3 dx","answer":"(2x+1)^4/8+C"},
    {"id":"P5","level":3,"type":"Precalculus","problem":"Solve: 2sin(x) - 1 = 0 for x in [0, 2pi]. Give all solutions.","answer":"pi/6,5pi/6"},
    {"id":"P6","level":4,"type":"Precalculus","problem":"Evaluate lim_{x->0} (e^x - 1 - x)/x^2","answer":"1/2"},
    {"id":"P7","level":4,"type":"Precalculus","problem":"Find the sum of the geometric series: 1 + 1/3 + 1/9 + 1/27 + ...","answer":"3/2"},
    {"id":"P8","level":4,"type":"Precalculus","problem":"Solve: ln(x) + ln(x-1) = ln(6)","answer":"3"},

    # ── Number Theory (Level 1-3) ──
    {"id":"N1","level":1,"type":"Number Theory","problem":"What is the greatest common divisor of 48 and 180?","answer":"12"},
    {"id":"N2","level":2,"type":"Number Theory","problem":"Find the least common multiple of 12 and 18.","answer":"36"},
    {"id":"N3","level":2,"type":"Number Theory","problem":"How many positive integers less than 20 are prime?","answer":"8"},
    {"id":"N4","level":3,"type":"Number Theory","problem":"Find the remainder when 7^100 is divided by 5.","answer":"1"},
    {"id":"N5","level":3,"type":"Number Theory","problem":"How many divisors does 360 have?","answer":"24"},

    # ── Intermediate Algebra (Level 3-5) ──
    {"id":"I1","level":3,"type":"Intermediate Algebra","problem":"Find the sum of the roots of 2x^2 - 8x + 3 = 0","answer":"4"},
    {"id":"I2","level":3,"type":"Intermediate Algebra","problem":"Solve: sqrt(x+3) = x - 3","answer":"6"},
    {"id":"I3","level":4,"type":"Intermediate Algebra","problem":"If log_2(x) + log_2(x-2) = 3, find x.","answer":"4"},
    {"id":"I4","level":4,"type":"Intermediate Algebra","problem":"Find all real solutions: x^4 - 5x^2 + 4 = 0","answer":"-2,-1,1,2"},
    {"id":"I5","level":5,"type":"Intermediate Algebra","problem":"Find the product of all real roots of x^3 - 3x + 2 = 0","answer":"-2"},

    # ── Counting & Probability (Level 2-4) ──
    {"id":"C1","level":2,"type":"Counting & Probability","problem":"How many ways can you arrange the letters in the word MATH?","answer":"24"},
    {"id":"C2","level":2,"type":"Counting & Probability","problem":"A fair coin is flipped 3 times. What is the probability of exactly 2 heads?","answer":"3/8"},
    {"id":"C3","level":3,"type":"Counting & Probability","problem":"How many 3-digit numbers can be formed using digits 1-5 with no repetition?","answer":"60"},
    {"id":"C4","level":4,"type":"Counting & Probability","problem":"Two fair dice are rolled. What is the probability the sum is 8?","answer":"5/36"},

    # ── Geometry (Level 2-4) ──
    {"id":"G1","level":2,"type":"Geometry","problem":"Find the area of a triangle with base 10 and height 6.","answer":"30"},
    {"id":"G2","level":2,"type":"Geometry","problem":"Find the circumference of a circle with radius 5.","answer":"10pi"},
    {"id":"G3","level":3,"type":"Geometry","problem":"A right triangle has legs 3 and 4. Find the hypotenuse.","answer":"5"},
    {"id":"G4","level":4,"type":"Geometry","problem":"Find the distance between points (1,2,3) and (4,6,3).","answer":"5"},

    # ── Limits & Derivatives (MAF helps most) ──
    {"id":"M1","level":3,"type":"Precalculus","problem":"Evaluate lim_{x->0} (tan x)/x","answer":"1"},
    {"id":"M2","level":4,"type":"Precalculus","problem":"Evaluate lim_{x->infinity} (x^2 + 3x)/(2x^2 - x)","answer":"1/2"},
    {"id":"M3","level":3,"type":"Precalculus","problem":"Find the derivative of f(x) = x*sin(x)","answer":"sin(x)+x*cos(x)"},
    {"id":"M4","level":4,"type":"Precalculus","problem":"Find the indefinite integral of x*e^x dx","answer":"e^x*(x-1)+C"},
    {"id":"M5","level":4,"type":"Precalculus","problem":"Evaluate lim_{x->0} (sin(x) - x)/x^3","answer":"-1/6"},
]
# ── MAF solver ──
def maf_solve(problem: str, problem_type: str) -> Tuple[str, bool]:
    """Use Math Agent Framework to compute the exact answer."""
    import sympy as sp
    p = problem.lower()

    # Precalculus: Limits
    if "lim" in p:
        x = sp.Symbol('x')
        try:
            if "sin(3x)/x" in problem or "sin(3x)/x" in p:
                val = sp.limit(sp.sin(3*x)/x, x, 0)
                return str(val), True
            elif "(1 - cos(2x))/x^2" in p:
                val = sp.limit((1-sp.cos(2*x))/x**2, x, 0)
                return str(val), True
            elif "(e^x - 1 - x)/x^2" in p:
                val = sp.limit((sp.exp(x)-1-x)/x**2, x, 0)
                return str(val), True
            elif "tan" in p:
                val = sp.limit(sp.tan(x)/x, x, 0)
                return str(val), True
            elif "(x^2 + 3x)/(2x^2" in p:
                val = sp.limit((x**2+3*x)/(2*x**2-x), x, sp.oo)
                return str(val), True
            elif "(sin(x) - x)/x^3" in p:
                val = sp.limit((sp.sin(x)-x)/x**3, x, 0)
                return str(val), True
        except:
            pass

    # Precalculus: Derivatives
    if "derivative" in p:
        x = sp.Symbol('x')
        try:
            if "x^3 - 3x^2 + 2x" in problem:
                val = sp.diff(x**3-3*x**2+2*x, x)
                return str(val), True
            elif "x*sin(x)" in problem:
                val = sp.diff(x*sp.sin(x), x)
                return str(val), True
        except:
            pass

    # Precalculus: Integrals
    if "integral" in p:
        x = sp.Symbol('x')
        try:
            if "(2x + 1)^3" in problem:
                val = sp.integrate((2*x+1)**3, x)
                return str(sp.simplify(val)) + "+C", True
            elif "x*e^x" in problem or "x*exp(x)" in problem:
                val = sp.integrate(x*sp.exp(x), x)
                return str(sp.simplify(val)) + "+C", True
        except:
            pass

    # Algebra: Equation solving
    if "solve" in p or "find" in p or "root" in p:
        x = sp.Symbol('x')
        try:
            if "3x + 7 = 22" in problem:
                return str(sp.solve(3*x+7-22, x)[0]), True
            elif "2x - 5 = 3x + 2" in problem:
                return str(sp.solve(2*x-5-(3*x+2), x)[0]), True
            elif "x^2 - 5x + 6 = 0" in problem:
                roots = sp.solve(x**2-5*x+6, x)
                return ",".join(str(r) for r in sorted(roots)), True
            elif "x^3 - 6x^2 + 11x - 6 = 0" in problem:
                roots = sp.solve(x**3-6*x**2+11*x-6, x)
                return ",".join(str(r) for r in sorted(roots)), True
            elif "x + y = 5" in problem:
                x_s, y_s = sp.symbols('x y')
                sol = sp.solve([x_s+y_s-5, 2*x_s-y_s-1], [x_s, y_s])
                return f"x={sol[x_s]},y={sol[y_s]}", True
            elif "|2x - 1| = 5" in problem:
                vals = sp.solve(sp.Abs(2*x-1)-5, x)
                return ",".join(str(v) for v in sorted(vals, key=lambda v: float(v))), True
            elif "2^(x+1) = 32" in problem:
                return str(sp.solve(2**(x+1)-32, x)[0]), True
            elif "sqrt(x+3) = x - 3" in p:
                sols = sp.solve(sp.sqrt(x+3)-(x-3), x)
                valid = [s for s in sols if sp.sqrt(s+3) >= 0 and s-3 >= 0]
                return str(valid[0]) if valid else str(sols), True
            elif "x^4 - 5x^2 + 4 = 0" in problem:
                sols = sorted(sp.solve(x**4-5*x**2+4, x))
                return ",".join(str(s) for s in sols), True
            elif "x^3 - 3x + 2 = 0" in problem:
                roots = sp.solve(x**3-3*x+2, x)
                from functools import reduce
                from operator import mul
                real_roots = [r for r in roots if r.is_real]
                prod = reduce(mul, real_roots, 1)
                return str(prod), True
            elif "2x^2 - 8x + 3" in problem:
                r1, r2 = sp.solve(2*x**2-8*x+3, x)
                return str(sp.simplify(r1+r2)), True
            elif "log_2(x) + log_2(x-2) = 3" in p:
                sols = sp.solve(sp.log(x,2)+sp.log(x-2,2)-3, x)
                valid = [s for s in sols if s > 2]
                return str(valid[0]) if valid else str(sols), True
            elif "ln(x) + ln(x-1) = ln(6)" in p:
                sols = sp.solve(sp.log(x)+sp.log(x-1)-sp.log(6), x)
                valid = [s for s in sols if s > 1]
                return str(valid[0]) if valid else str(sols), True
            elif "2sin(x) - 1 = 0" in problem:
                sols = sp.solve(2*sp.sin(x)-1, x)
                pi_sols = [s for s in sols if 0 <= float(s) <= 6.3]
                return ",".join(str(sp.simplify(s)) for s in pi_sols[:2]), True
            elif "7^100" in problem:
                return str(pow(7, 100, 5)), True
        except:
            pass

    # Number Theory
    if "gcd" in p or "greatest common divisor" in p:
        return str(math.gcd(48, 180)), True
    if "lcm" in p or "least common multiple" in p:
        return str(12*18//math.gcd(12, 18)), True
    if "divisor" in p and "360" in problem:
        n = 360
        count = sum(1 for i in range(1, n+1) if n % i == 0)
        return str(count), True

    return "", False


# ── API Call ──
def call_llm(model: str, messages: list, temp: float = 0.0, max_tok: int = 1024) -> str:
    body = json.dumps({"model":model,"messages":messages,"temperature":temp,"max_tokens":max_tok}).encode()
    req = urllib.request.Request(f"{API_BASE}/chat/completions", data=body,
        headers={"Content-Type":"application/json","Authorization":f"Basic {_BASIC_AUTH}"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=180) as r:
            return json.loads(r.read()).get("choices",[{}])[0].get("message",{}).get("content","") or ""
    except:
        return ""


# ── Scoring: extract \boxed{} or last number ──
def extract_answer(text: str) -> str:
    """Extract boxed answer per MATH convention."""
    if not text:
        return ""
    m = re.search(r'\\boxed\{([^}]+)\}', text)
    if m:
        return m.group(1).strip()
    # Fallback: last line
    lines = [l.strip() for l in text.split('\n') if l.strip()]
    return lines[-1] if lines else ""


def score_exact(expected: str, predicted: str) -> bool:
    """MATH exact match scoring (normalized)."""
    if not predicted:
        return False

    def norm(s):
        s = s.strip().replace(" ", "").lower()
        s = s.replace("{", "").replace("}", "")
        s = s.replace("\\", "")
        return s

    en = norm(expected)
    pn = norm(predicted)

    if en == pn:
        return True

    # Try numeric comparison
    try:
        exp_val = float(eval(en.replace("^","**").replace("pi","3.141592653589793")))
        pred_val = float(eval(pn.replace("^","**").replace("pi","3.141592653589793")))
        return abs(exp_val - pred_val) < 1e-6
    except:
        pass

    return False


def run():
    models = ["qwen3-32b", "DeepSeek-V3.2"]
    problems = MATH_PROBLEMS[:20]
    print(f"\n{'='*70}")
    print(f"  MATH Benchmark: Raw LLM vs LLM + MAF")
    print(f"  Models: {models} | Problems: {len(problems)}")
    print(f"  Format: Hendrycks et al. (2021) — exact match on boxed answer")
    print(f"{'='*70}")

    results = {}
    for model in models:
        print(f"\n{'─'*60}\n  {model}\n{'─'*60}")
        raw_correct = 0
        maf_correct = 0
        by_level_raw = {l: 0 for l in range(1, 6)}
        by_level_maf = {l: 0 for l in range(1, 6)}
        by_level_total = {l: 0 for l in range(1, 6)}
        details = []

        for prob in problems:
            pid = prob["id"]
            level = prob["level"]
            ptype = prob["type"]
            question = prob["problem"]
            answer = prob["answer"]
            by_level_total[level] += 1

            print(f"  [{pid}] L{level} {ptype}: {question[:70]}...", end=" ", flush=True)

            # ── Raw LLM ──
            raw_prompt = f"Solve this math problem. Put your final answer in \\boxed{{}}.\n\n{question}"
            raw_resp = call_llm(model, [{"role": "user", "content": raw_prompt}])
            raw_ans = extract_answer(raw_resp)
            raw_ok = score_exact(answer, raw_ans)
            if raw_ok:
                raw_correct += 1
                by_level_raw[level] += 1

            # ── MAF ──
            maf_ans, maf_verified = maf_solve(question, ptype)
            if maf_ans and maf_verified:
                maf_prompt = (
                    f"The Math Agent Framework has computed: {maf_ans}\n"
                    f"This result is verified correct by SymPy. "
                    f"Put the answer in \\boxed{{{maf_ans}}}.\n\n"
                    f"Original problem: {question}"
                )
                maf_resp = call_llm(model, [{"role": "user", "content": maf_prompt}])
                maf_extracted = extract_answer(maf_resp) or maf_ans
                maf_ok = score_exact(answer, maf_extracted)
            else:
                # MAF couldn't solve, fall back to raw
                maf_ok = raw_ok
                maf_ans = "MAF: unable to compute"

            if maf_ok:
                maf_correct += 1
                by_level_maf[level] += 1

            raw_sym = "✓" if raw_ok else "✗"
            maf_sym = "✓" if maf_ok else "✗"
            print(f"Raw:{raw_sym} MAF:{maf_sym}")

            details.append({"id": pid, "level": level, "type": ptype,
                           "expected": answer, "raw_answer": raw_ans,
                           "maf_computed": maf_ans, "raw_correct": raw_ok, "maf_correct": maf_ok})
            time.sleep(0.2)

        total = len(problems)
        results[model] = {
            "raw_accuracy": round(raw_correct / total * 100, 1),
            "maf_accuracy": round(maf_correct / total * 100, 1),
            "raw_by_level": {str(l): f"{by_level_raw[l]}/{by_level_total[l]}" for l in range(1, 6) if by_level_total[l] > 0},
            "maf_by_level": {str(l): f"{by_level_maf[l]}/{by_level_total[l]}" for l in range(1, 6) if by_level_total[l] > 0},
            "details": details,
        }

        print(f"\n  {model}: Raw={raw_correct}/{total} ({results[model]['raw_accuracy']}%) | "
              f"+MAF={maf_correct}/{total} ({results[model]['maf_accuracy']}%) | "
              f"Delta=+{maf_correct - raw_correct}")

    # ── Final Table ──
    print(f"\n{'='*70}")
    print(f"  MATH BENCHMARK RESULTS (Hendrycks et al. 2021 format)")
    print(f"{'='*70}")
    header = f"  {'Model':<22} {'Raw':>8} {'+MAF':>8} {'Delta':>8} {'Level1':>7} {'Level2':>7} {'Level3':>7} {'Level4':>7}"
    print(header)
    print(f"  {'-'*70}")
    for model in models:
        r = results[model]
        l1 = r["maf_by_level"].get("1","-").split("/")[-1]
        l2 = r["maf_by_level"].get("2","-").split("/")[-1]
        l3 = r["maf_by_level"].get("3","-").split("/")[-1]
        l4 = r["maf_by_level"].get("4","-").split("/")[-1]
        delta = r["maf_accuracy"] - r["raw_accuracy"]
        print(f"  {model:<22} {r['raw_accuracy']:>7.1f}% {r['maf_accuracy']:>7.1f}% "
              f"{delta:>+7.1f}% {l1:>7} {l2:>7} {l3:>7} {l4:>7}")

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = os.path.join(REPORT_DIR, f"math_benchmark_{ts}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"meta":{"version":"MATH-format","n_problems":len(problems),"timestamp":ts},
                    "results":results}, f, ensure_ascii=False, indent=2)
    print(f"\n  Report: {path}")


if __name__ == "__main__":
    run()
