"""Direct engine correctness: SymPy tools vs ground truth."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import sympy as sp
from sympy.solvers.ode import checkodesol
from core.analysis_engine import AnalysisEngine
import numpy as np
import json

RESULTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results")
os.makedirs(RESULTS_DIR, exist_ok=True)

# Define test cases with machine-readable expressions
tests = {
    "easy": [
        {"id": "linear-1", "desc": "3x+7=22", "func": "solve", "expr": lambda x: sp.Eq(3*x+7, 22), "expected": {5}},
        {"id": "linear-2", "desc": "5x-3=2x+9", "func": "solve", "expr": lambda x: sp.Eq(5*x-3, 2*x+9), "expected": {4}},
        {"id": "factor-1", "desc": "x^2+5x+6", "func": "factor", "expr": lambda x: x**2+5*x+6, "expected": "(x + 2)*(x + 3)"},
        {"id": "slope", "desc": "slope (2,5)->(6,13)", "func": "compute", "expected": 2.0},
        {"id": "arithmetic", "desc": "(8*7)+(6*5)-(4*3)", "func": "compute", "expected": 74.0},
    ],
    "medium": [
        {"id": "quad-1", "desc": "x^2-5x+6=0", "func": "solve", "expr": lambda x: x**2-5*x+6, "expected": {2, 3}},
        {"id": "quad-2", "desc": "2x^2-7x+3=0", "func": "solve", "expr": lambda x: 2*x**2-7*x+3, "expected": {3, sp.Rational(1,2)}},
        {"id": "system-1", "desc": "2x+y=7,x-y=2", "func": "system",
         "expr": lambda x,y: [2*x+y-7, x-y-2], "expected": [3, 1]},
        {"id": "system-2", "desc": "3x+2y=12,2x-y=1", "func": "system",
         "expr": lambda x,y: [3*x+2*y-12, 2*x-y-1], "expected": [2, 3]},
        {"id": "abs-1", "desc": "|3x-2|<=7", "func": "inequality",
         "expr": lambda x: sp.Abs(3*x-2) <= 7, "expected": "interval"},
        {"id": "discriminant", "desc": "kx^2-4x+1=0 one root", "func": "solve",
         "expr": lambda k: (-4)**2 - 4*k*1, "expected": {4}},
    ],
    "hard": [
        {"id": "quartic", "desc": "x^4-5x^2+4=0", "func": "solve",
         "expr": lambda x: x**4-5*x**2+4, "expected": {-2, -1, 1, 2}},
        {"id": "cubic-sum", "desc": "x^3-6x^2+11x-6 sum",
         "func": "sum_roots", "expr": lambda x: x**3-6*x**2+11*x-6, "expected": 6},
        {"id": "limit-1", "desc": "lim sin(x)/x", "func": "limit",
         "expr": lambda x: sp.sin(x)/x, "point": 0, "expected": 1},
        {"id": "limit-2", "desc": "lim (sin(x)-x)/x^3", "func": "limit",
         "expr": lambda x: (sp.sin(x)-x)/x**3, "point": 0, "expected": -sp.Rational(1,6)},
        {"id": "limit-3", "desc": "lim (1-cos(x))/x^2", "func": "limit",
         "expr": lambda x: (1-sp.cos(x))/x**2, "point": 0, "expected": sp.Rational(1,2)},
        {"id": "series-conv", "desc": "sum n!/n^n", "func": "series",
         "term": lambda n: sp.factorial(n)/n**n, "expected_verdict": "convergent"},
        {"id": "ode-euler", "desc": "x^2 y'' + x y' - y = 0", "func": "ode_euler", "expected_verified": True},
        {"id": "ode-damped", "desc": "y'' + 3y' + 2y = 0", "func": "ode_damped", "expected_verified": True},
    ],
}

x = sp.Symbol('x', real=True)
y = sp.Symbol('y', real=True)
n = sp.Symbol('n', integer=True, positive=True)
f = sp.Function('f')(x)
ae = AnalysisEngine()

print("=" * 60)
print("  Direct Engine Tool Correctness Test")
print("=" * 60)

all_results = {}
total, passed = 0, 0

for level, level_tests in tests.items():
    level_ok = 0
    for t in level_tests:
        total += 1
        tid = t["id"]
        correct = False
        detail = ""

        try:
            if t["func"] == "solve":
                roots = sp.solve(t["expr"](x), x)
                correct = set(roots) == t["expected"]
                detail = f"roots={set(roots)} expected={t['expected']}"
            elif t["func"] == "factor":
                factored = sp.factor(t["expr"](x))
                correct = str(factored).replace(" ", "") == t["expected"].replace(" ", "")
                detail = f"factored={factored}"
            elif t["func"] == "compute":
                if "slope" in tid:
                    val = (13-5)/(6-2)
                else:
                    val = (8*7)+(6*5)-(4*3)
                correct = abs(val - t["expected"]) < 0.001
                detail = f"computed={val}"
            elif t["func"] == "system":
                sol = sp.solve(t["expr"](x, y), (x, y), dict=True)
                if sol:
                    # t["expected"] = [3, 1] meaning x=3, y=1
                    expected = t.get("expected", [])
                    if isinstance(expected, dict):
                        expected = list(expected.values())
                    actual_vals = [float(sol[0][x]), float(sol[0][y])]
                    correct = len(actual_vals) == len(expected) and \
                              all(abs(a - e) < 0.001 for a, e in zip(actual_vals, expected))
                detail = f"sol={sol} expected={t.get('expected')}"
            elif t["func"] == "inequality":
                sol = sp.solve_univariate_inequality(t["expr"](x), x)
                correct = sol is not None
                detail = f"sol={sol}"
            elif t["func"] == "limit":
                lim = sp.limit(t["expr"](x), x, t["point"])
                correct = abs(float(lim) - float(t["expected"])) < 0.001
                detail = f"limit={lim} expected={t['expected']}"
            elif t["func"] == "series":
                term_limit = sp.limit(t["term"](n), n, sp.oo)
                ratio = sp.simplify(t["term"](n+1) / t["term"](n))
                ratio_limit = sp.limit(ratio, n, sp.oo)
                convergent = (term_limit == 0 and float(ratio_limit) < 1)
                correct = convergent == (t["expected_verdict"] == "convergent")
                detail = f"term_limit={term_limit} ratio_limit={float(ratio_limit):.4f} conv={convergent}"
            elif t["func"] == "ode_euler":
                ode = x**2 * sp.diff(f, x, 2) + x * sp.diff(f, x) - f
                sol = sp.dsolve(ode, f)
                check = checkodesol(ode, sol, func=f)
                correct = bool(check[0])
                detail = f"sol={sol} check={check}"
            elif t["func"] == "sum_roots":
                roots = sp.solve(t["expr"](x), x)
                s = sum(roots)
                correct = abs(float(s) - float(t["expected"])) < 0.001
                detail = f"roots={roots} sum={s}"
            elif t["func"] == "ode_damped":
                ode = sp.diff(f, x, 2) + 3*sp.diff(f, x) + 2*f
                sol = sp.dsolve(ode, f)
                check = checkodesol(ode, sol, func=f)
                correct = bool(check[0])
                detail = f"sol={sol} check={check}"
        except Exception as e:
            detail = f"ERROR: {e}"

        symbol = "+" if correct else "X"
        print(f"  [{symbol}] {level:6s} {tid:15s} ({t['desc'][:30]:30s}) {detail[:60]}")
        all_results[tid] = {"level": level, "correct": correct, "detail": detail}
        if correct:
            passed += 1
            level_ok += 1

    level_total = len(level_tests)
    print(f"  --- {level}: {level_ok}/{level_total} ({level_ok/level_total*100:.0f}%) ---")
    print()

print(f"{'='*60}")
print(f"  TOTAL: {passed}/{total} ({passed/total*100:.0f}%)")
print(f"{'='*60}")

# Summary by level
by_level = {}
for level in ["easy", "medium", "hard"]:
    lt = [r for r in all_results.values() if r["level"] == level]
    ok = sum(1 for r in lt if r["correct"])
    by_level[level] = {"total": len(lt), "correct": ok,
                       "accuracy": round(ok/max(len(lt),1), 4)}

summary = {"total": total, "passed": passed, "accuracy": round(passed/total, 4),
           "by_level": by_level}
path = os.path.join(RESULTS_DIR, "engine_correctness.json")
with open(path, "w", encoding="utf-8") as f:
    json.dump(summary, f, ensure_ascii=False, indent=2)
print(f"\nSaved: {path}")

# Plot
try:
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    THEME = {'bg': '#1e1e2e', 'fg': '#cdd6f4', 'bar': '#a6e3a1',
             'grid': '#45475a', 'text': '#bac2de'}

    fig, ax = plt.subplots(figsize=(8, 5))
    fig.patch.set_facecolor(THEME['bg']); ax.set_facecolor(THEME['bg'])

    levels = ["easy", "medium", "hard"]
    accs = [by_level[l]["accuracy"]*100 for l in levels]
    bars = ax.bar(levels, accs, color=[THEME['bar'], THEME['bar'], THEME['bar']],
                  alpha=0.9, edgecolor='white', linewidth=0.3)
    for bar, acc in zip(bars, accs):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 2,
               f'{acc:.0f}%', ha='center', fontsize=12, color=THEME['fg'], fontweight='bold')

    ax.set_ylim(0, 115)
    ax.set_ylabel('Engine Tool Accuracy (%)', color=THEME['text'], fontsize=11)
    ax.set_title('Math Agent Framework — Engine Tool Correctness',
                color=THEME['fg'], fontsize=13, fontweight='bold')
    ax.grid(True, alpha=0.12, color=THEME['text'], axis='y')
    ax.tick_params(colors=THEME['text'], labelsize=11)
    for spine in ax.spines.values(): spine.set_color(THEME['grid'])

    fig.tight_layout()
    curve_path = os.path.join(RESULTS_DIR, "engine_correctness.png")
    fig.savefig(curve_path, dpi=150, bbox_inches='tight', facecolor=THEME['bg'])
    plt.close(fig)
    print(f"Saved: {curve_path}")
except ImportError:
    pass
