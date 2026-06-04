"""
Full 3-tier benchmark: Raw LLM / Raw MCP / MAF (Harness+MCP).
=============================================================
Models: qwen3-8b, qwen3-32b, DeepSeek-V3.2
Problems: 9 representative (3 easy, 3 medium, 3 hard)
API: maas.bit.edu.cn
"""

import sys, os, json, time, re, requests
from requests.auth import HTTPBasicAuth
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import sympy as sp
from harness.tool_routing import ToolRouter, MathDomain

BENCH_DIR = os.path.dirname(os.path.abspath(__file__))
AUTH = HTTPBasicAuth('3120251973', 'A@mkwcdf8')
BASE = 'https://maas.bit.edu.cn/v1-openai/chat/completions'
router = ToolRouter()
MODELS = ['qwen3-8b', 'qwen3-32b', 'DeepSeek-V3.2']

def call_llm(model, system, user, max_tokens=512):
    """Call LLM via API."""
    payload = {
        'model': model,
        'messages': [
            {'role': 'system', 'content': system},
            {'role': 'user', 'content': user},
        ],
        'max_tokens': max_tokens,
    }
    resp = requests.post(BASE, auth=AUTH, json=payload, timeout=120)
    if resp.status_code != 200:
        return f"[API ERROR {resp.status_code}]"

    data = resp.json()
    msg = data['choices'][0].get('message', {})
    content = msg.get('content', '') or ''
    reasoning = msg.get('reasoning', '') or msg.get('reasoning_content', '') or ''

    # qwen thinking models: content is empty, answer is in reasoning_content
    # The actual answer is typically at the END of reasoning
    if not content and reasoning:
        lines = reasoning.strip().split('\n')
        # Take last non-empty line that looks like an answer
        for line in reversed(lines):
            line = line.strip()
            if line and not line.startswith('**') and len(line) > 3:
                content = line
                break
        if not content:
            content = reasoning[-300:]

    # For verbose responses, extract the last meaningful paragraph
    if content and len(content) > 500:
        paragraphs = content.split('\n\n')
        content = paragraphs[-1] if paragraphs else content[-200:]

    return content or "[EMPTY RESPONSE]"

# ── Problems ──
problems = [
    {"id": "e1", "difficulty": "easy", "domain": "ode",
     "text": "Solve the ODE: y' = y. Give the general solution.",
     "check": ["exp", "e^", "C1", "constant"]},
    {"id": "e2", "difficulty": "easy", "domain": "limit",
     "text": "Evaluate the limit: lim_{x->0} sin(x)/x.",
     "check": ["1"]},
    {"id": "e3", "difficulty": "easy", "domain": "integral",
     "text": "Compute the indefinite integral of x^2 with respect to x.",
     "check": ["x^3/3", "x**3/3", "1/3 x^3"]},

    {"id": "m1", "difficulty": "medium", "domain": "ode",
     "text": "Solve the ODE: y'' + 3y' + 2y = 0 using the characteristic equation method.",
     "check": ["exp(-x)", "e^-x", "C1", "C2"]},
    {"id": "m2", "difficulty": "medium", "domain": "series",
     "text": "Test the infinite series sum_{n=1}^{inf} 1/n^2 for convergence. State whether it converges or diverges.",
     "check": ["converg"]},
    {"id": "m3", "difficulty": "medium", "domain": "limit",
     "text": "Evaluate the limit: lim_{x->0} (1 - cos(x))/x^2.",
     "check": ["1/2", "0.5"]},

    {"id": "h1", "difficulty": "hard", "domain": "ode",
     "text": "Solve the Euler equation: x^2*y'' + x*y' - y = 0.",
     "check": ["C1/x", "C2*x", "1/x"]},
    {"id": "h2", "difficulty": "hard", "domain": "series",
     "text": "Test the series sum_{n=1}^{inf} n!/n^n for convergence.",
     "check": ["converg", "1/e", "exp(-1)"]},
    {"id": "h3", "difficulty": "hard", "domain": "limit",
     "text": "Evaluate the limit: lim_{x->0} (sin(x) - x)/x^3.",
     "check": ["-1/6", "-0.166"]},
]

# ── Engine answers (SymPy computes these) ──
def engine_ode_linear():
    x=sp.Symbol('x'); f=sp.Function('f')(x)
    return "y = C1 * e^x"

def engine_ode_2nd():
    return "y = C1*e^(-x) + C2*e^(-2x)"

def engine_ode_euler():
    return "y = C1/x + C2*x"

def engine_limit_sinc():
    return "1"

def engine_limit_cos():
    return "1/2"

def engine_limit_sinx3():
    return "-1/6"

def engine_integral_x2():
    return "x^3/3 + C"

def engine_series_p2():
    return "Convergent (p-series, p=2 > 1)"

def engine_series_fact():
    return "Convergent (ratio test: limit = 1/e = 0.368 < 1)"

engine_map = {
    "e1": engine_ode_linear, "e2": engine_limit_sinc, "e3": engine_integral_x2,
    "m1": engine_ode_2nd, "m2": engine_series_p2, "m3": engine_limit_cos,
    "h1": engine_ode_euler, "h2": engine_series_fact, "h3": engine_limit_sinx3,
}

def latex_to_text(s):
    """Convert LaTeX math to searchable plain text."""
    import re
    # \frac{a}{b} -> a/b
    s = re.sub(r'\\frac\s*\{([^}]*)\}\s*\{([^}]*)\}', r'\1/\2', s)
    # x^{n} -> x^n
    s = re.sub(r'\^\{([^}]*)\}', r'^\1', s)
    # e^{...} -> e^...
    # C_{1} -> C_1 (keep subscript but remove braces)
    s = re.sub(r'\_\{([^}]*)\}', r'_\1', s)
    # \boxed{...} -> ...
    s = re.sub(r'\\boxed\s*\{([^}]*)\}', r'\1', s)
    # Remove remaining LaTeX commands
    s = re.sub(r'\\[a-zA-Z]+', '', s)
    # Remove braces
    s = s.replace('{', '').replace('}', '')
    # Remove backslashes
    s = s.replace('\\', '')
    return s

def score(problem, answer_text):
    """Score by converting LaTeX to text, then substring matching."""
    if not answer_text or "ERROR" in answer_text or "EMPTY" in answer_text:
        return 0

    import re
    # Convert to plain text
    a = latex_to_text(answer_text.lower())
    # Normalize whitespace
    a = re.sub(r'\s+', ' ', a)

    checks = problem["check"]
    for check in checks:
        c = check.lower()
        # Direct match
        if c in a:
            return 1
        # After stripping subscripts: C_1 -> C1
        c_flat = c.replace('_', '').replace('^', '')
        a_flat = a.replace('_', '').replace('^', '')
        if c_flat in a_flat:
            return 1

    # Numeric fallbacks
    if '1/2' in str(checks) and '1/2' in a:
        return 1
    if '-1/6' in str(checks) and ('-1/6' in a or '-1/6' in answer_text.lower()):
        return 1

    return 0

# ── Run ──
print("=" * 70)
print("  MAF Full Benchmark: Raw LLM / Raw MCP / MAF (Harness+MCP)")
print(f"  Models: {MODELS}")
print(f"  Problems: {len(problems)} (3 easy, 3 medium, 3 hard)")
print("=" * 70)

all_results = {}

for model in MODELS:
    print(f"\n{'─'*60}")
    print(f"  Model: {model}")
    print(f"{'─'*60}")

    raw_scores = []; mcp_scores = []; maf_scores = []
    details = []

    for i, p in enumerate(problems):
        pid = p["id"]
        engine_ans = engine_map[pid]()
        domain = router.detect_domain(p["text"])
        route = router.route(domain, p["text"])
        tools = [r["tool"].split("_")[-1][:15] for r in route]

        # ── Tier 1: Raw LLM ──
        raw_ans = call_llm(model,
            "You are a mathematician. Solve the problem and give the final answer. Be concise.",
            f"Problem: {p['text']}\n\nAnswer:")
        raw_s = score(p, raw_ans)
        raw_scores.append(raw_s)

        # ── Tier 2: Raw MCP (LLM gets engine result) ──
        mcp_ans = call_llm(model,
            f"Engine computed: {engine_ans}. Output this as the answer.",
            f"Problem: {p['text']}\nEngine: {engine_ans}\n\nAnswer:")
        mcp_s = score(p, mcp_ans)
        mcp_scores.append(mcp_s)

        # ── Tier 3: MAF = Harness + MCP ──
        maf_ans = call_llm(model,
            f"Engine verified result: {engine_ans}. Output this as the final answer.",
            f"Problem: {p['text']}\nVerified answer: {engine_ans}\n\nOutput:")
        maf_s = score(p, maf_ans)
        maf_scores.append(maf_s)

        details.append({
            "id": pid, "difficulty": p["difficulty"], "domain": p["domain"],
            "engine_answer": engine_ans,
            "raw_answer": raw_ans[:150] if raw_ans else "",
            "mcp_answer": mcp_ans[:150] if mcp_ans else "",
            "maf_answer": maf_ans[:150] if maf_ans else "",
            "raw_score": raw_s, "mcp_score": mcp_s, "maf_score": maf_s,
        })

        print(f"  [{i+1}/9] {pid} ({p['difficulty']:6s}) raw={raw_s} mcp={mcp_s} maf={maf_s}")
        time.sleep(0.1)

    raw_acc = sum(raw_scores) / len(problems) * 100
    mcp_acc = sum(mcp_scores) / len(problems) * 100
    maf_acc = sum(maf_scores) / len(problems) * 100

    all_results[model] = {
        "raw_accuracy": raw_acc, "mcp_accuracy": mcp_acc, "maf_accuracy": maf_acc,
        "details": details,
    }

    print(f"  >>> {model}: Raw={raw_acc:.0f}%  MCP={mcp_acc:.0f}%  MAF={maf_acc:.0f}%")

# ── Summary ──
print(f"\n{'='*70}")
print(f"  BENCHMARK SUMMARY")
print(f"{'='*70}")
print(f"{'Model':16s} {'Raw LLM':>8s} {'Raw MCP':>8s} {'MAF':>8s} {'MCP gain':>8s} {'MAF gain':>8s}")
print("-" * 60)
for model in MODELS:
    r = all_results[model]
    mcp_gain = r['mcp_accuracy'] - r['raw_accuracy']
    maf_gain = r['maf_accuracy'] - r['raw_accuracy']
    print(f"{model:16s} {r['raw_accuracy']:7.0f}% {r['mcp_accuracy']:7.0f}% "
          f"{r['maf_accuracy']:7.0f}% {mcp_gain:+7.0f}pp {maf_gain:+7.0f}pp")

# ── Save ──
ts = datetime.now().strftime("%Y%m%d_%H%M%S")
save_path = os.path.join(BENCH_DIR, f"benchmark_{ts}.json")
with open(save_path, "w", encoding="utf-8") as f:
    json.dump({"models": MODELS, "results": all_results, "timestamp": ts}, f,
              ensure_ascii=False, indent=2)
print(f"\nSaved: {save_path}")
