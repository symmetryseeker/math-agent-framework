#!/usr/bin/env python3
"""
MathReliability Benchmark v1 — Model Comparison Tool
=====================================================
Tests LLM models on mathematical reliability: planning, tool selection,
computation correctness, and verification pass rate.

Usage:
    python benchmarks/run_mr.py                          # auto-discover models
    python benchmarks/run_mr.py --model qwen2.5-7b      # test specific model
    python benchmarks/run_mr.py --models qwen2.5-7b,qwen2.5-14b  # test multiple
    python benchmarks/run_mr.py --quick                  # 10-problem quick scan
    python benchmarks/run_mr.py --report-only            # just show saved report

Platform: BIT MAAS (https://maas.bit.edu.cn/v1-openai)
"""

import sys, os, io, json, time, re, urllib.request, urllib.error
from datetime import datetime
from typing import Any, Dict, List, Optional

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.agent_loop import ToolExecutor

# ── Config ──
API_BASE = os.environ.get("MATH_BENCH_BASE_URL", "https://maas.bit.edu.cn/v1-openai")
API_KEY = os.environ.get("MATH_BENCH_API_KEY", "")
BENCH_DIR = os.path.dirname(os.path.abspath(__file__))
PROBLEMS_FILE = os.path.join(BENCH_DIR, "problems.json")
REPORT_DIR = os.path.join(BENCH_DIR, "reports")
os.makedirs(REPORT_DIR, exist_ok=True)


def fetch_models() -> List[str]:
    """Auto-discover available models from the API."""
    if not API_KEY:
        print("[WARN] No API key set. Set MATH_BENCH_API_KEY env var.")
        print("       Export: MATH_BENCH_API_KEY='your-key'")
        return []

    try:
        req = urllib.request.Request(
            f"{API_BASE}/models",
            headers={"Authorization": f"Bearer {API_KEY}"}
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
        models = []
        if isinstance(data, dict) and "data" in data:
            for m in data["data"]:
                models.append(m.get("id", ""))
        elif isinstance(data, list):
            for m in data:
                models.append(m.get("id", m) if isinstance(m, dict) else str(m))
        return sorted(models)
    except Exception as e:
        print(f"[WARN] Could not fetch model list: {e}")
        return []


def call_llm(model: str, system_prompt: str, user_message: str,
             temperature: float = 0.1, max_tokens: int = 2048) -> str:
    """Call the BIT MAAS API (OpenAI-compatible)."""
    body = json.dumps({
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
        "temperature": temperature,
        "max_tokens": max_tokens,
    }).encode("utf-8")

    req = urllib.request.Request(
        f"{API_BASE}/chat/completions",
        data=body,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {API_KEY}",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read())
        return data.get("choices", [{}])[0].get("message", {}).get("content", "")
    except urllib.error.HTTPError as e:
        return f"[ERROR {e.code}] {e.reason}"
    except Exception as e:
        return f"[ERROR] {e}"


SYSTEM_PROMPT = """You are a mathematical reasoning agent. You solve math problems by calling tools.

Available tools:
- ODE classification and solving (separable, linear, 2nd order, systems)
- PDE classification (elliptic/parabolic/hyperbolic)
- Limit evaluation (direct, L'Hopital, numerical verification)
- Series convergence testing (ratio, root, comparison tests)
- Integration (direct, by-parts, partial fractions, with verification)
- Optimization (FOC, SOC, Hessian classification)
- Special functions (Gamma, Beta, Zeta)

For each problem:
1. Classify the problem type
2. Name the specific tool(s) you would use
3. Give the final answer
4. Note whether verification is needed

Respond in this format:
CLASSIFICATION: <problem type>
TOOLS: <tool names>
ANSWER: <final answer>
VERIFICATION: <yes/no and method>"""


def score_response(problem: dict, llm_response: str, executor: ToolExecutor) -> Dict[str, Any]:
    """Score an LLM response against expected output."""
    scores = {"model_answer": llm_response[:500], "scores": {}}

    # 1. Classification accuracy (did LLM identify the right problem type?)
    expected_cat = problem["category"]
    response_lower = llm_response.lower()
    cat_keywords = {
        "ode": ["ode", "differential", "ordinary"],
        "analysis": ["limit", "series", "integral", "convergence"],
        "pde": ["pde", "partial", "heat", "wave", "laplace"],
        "optimization": ["optim", "foc", "soc", "hessian", "minimum", "maximum"],
        "special": ["gamma", "beta", "zeta", "stirling", "asymptotic", "oscillator"],
    }
    kw = cat_keywords.get(expected_cat, [])
    score_classification = any(k in response_lower for k in kw)
    scores["scores"]["classification"] = 1.0 if score_classification else 0.0

    # 2. Tool selection (did LLM name appropriate tools?)
    expected_tools = problem.get("expected_tools", [])
    tool_mentions = 0
    for tool in expected_tools:
        short_name = tool.replace("math_ode_solver_", "").replace("math_", "")
        if short_name in response_lower or tool.lower() in response_lower:
            tool_mentions += 1
    score_tools = tool_mentions / max(len(expected_tools), 1)
    scores["scores"]["tool_selection"] = score_tools

    # 3. Answer correctness (does answer match expected pattern?)
    if problem.get("expected_answer_pattern"):
        pattern = problem["expected_answer_pattern"]
        match = re.search(pattern, response_lower, re.IGNORECASE)
        scores["scores"]["correctness"] = 1.0 if match else 0.0
    else:
        scores["scores"]["correctness"] = 0.5  # unknown, give partial

    # 4. Verification awareness
    verify_method = problem.get("verification", "")
    score_verify = 0.0
    if "verif" in response_lower or "check" in response_lower:
        score_verify = 0.5  # mentioned verification
        if verify_method and verify_method in response_lower:
            score_verify = 1.0  # named the right method
    scores["scores"]["verification_awareness"] = score_verify

    # Overall
    s = scores["scores"]
    scores["overall"] = round(
        0.25 * s["classification"] + 0.30 * s["tool_selection"]
        + 0.30 * s["correctness"] + 0.15 * s["verification_awareness"], 4
    )
    return scores


def run_benchmark(models: List[str], quick: bool = False, limit: int = 0):
    """Run the full benchmark across all models."""
    with open(PROBLEMS_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    problems = data["problems"]
    if quick:
        problems = problems[:10]
    elif limit > 0:
        problems = problems[:limit]

    print(f"\n{'='*70}")
    print(f"  MathReliability Benchmark v1")
    print(f"  Platform: {API_BASE}")
    print(f"  Models: {len(models)} | Problems: {len(problems)}")
    print(f"{'='*70}\n")

    executor = ToolExecutor()
    report = {
        "meta": {
            "benchmark": "MathReliability-v1",
            "platform": API_BASE,
            "timestamp": datetime.now().isoformat(),
            "total_problems": len(problems),
        },
        "models": {},
        "summary": {},
    }

    for model in models:
        print(f"\n{'─'*60}")
        print(f"  Testing: {model}")
        print(f"{'─'*60}")

        model_results = []
        category_scores = {}

        for i, problem in enumerate(problems):
            pid = problem["id"]
            cat = problem["category"]
            diff = problem["difficulty"]
            prob_text = problem["problem"]

            print(f"  [{i+1}/{len(problems)}] {pid} ({diff})...", end=" ", flush=True)

            try:
                response = call_llm(model, SYSTEM_PROMPT, prob_text)
                scores = score_response(problem, response, executor)
                overall = scores["overall"]
                status = "✓" if overall >= 0.6 else "✗"
                print(f"{status} {overall:.2f}")
            except Exception as e:
                scores = {"model_answer": "", "scores": {}, "overall": 0.0, "error": str(e)}
                print(f"✗ ERROR: {e}")

            scores["problem_id"] = pid
            scores["category"] = cat
            scores["difficulty"] = diff
            model_results.append(scores)

            # Track category scores
            if cat not in category_scores:
                category_scores[cat] = []
            category_scores[cat].append(scores["overall"])

            time.sleep(0.3)  # rate limiting

        # Model summary
        all_scores = [r["overall"] for r in model_results]
        avg_score = round(sum(all_scores) / len(all_scores), 4) if all_scores else 0

        model_summary = {
            "model": model,
            "overall_avg": avg_score,
            "total_problems": len(model_results),
            "pass_rate": round(sum(1 for s in all_scores if s >= 0.6) / len(all_scores) * 100, 1) if all_scores else 0,
            "by_category": {c: round(sum(v)/len(v), 4) for c, v in category_scores.items()},
            "by_difficulty": {},
        }

        for diff in ["easy", "medium", "hard"]:
            diff_scores = [r["overall"] for r in model_results if r.get("difficulty") == diff]
            if diff_scores:
                model_summary["by_difficulty"][diff] = round(sum(diff_scores) / len(diff_scores), 4)

        report["models"][model] = {
            "summary": model_summary,
            "details": model_results,
        }
        report["summary"][model] = model_summary

        print(f"\n  {model}: avg={avg_score:.3f}, pass_rate={model_summary['pass_rate']:.1f}%")
        print(f"  By category: {model_summary['by_category']}")

    # Save report
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = os.path.join(REPORT_DIR, f"mr_report_{timestamp}.json")
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2, default=str)

    # Print comparison table
    print(f"\n{'='*70}")
    print(f"  COMPARISON TABLE")
    print(f"{'='*70}")
    header = f"  {'Model':<25} {'Avg':>7} {'Pass%':>7}  {'ODE':>6} {'Lim':>6} {'Int':>6} {'PDE':>6} {'Opt':>6}"
    print(header)
    print(f"  {'-'*70}")
    for model, info in report["models"].items():
        s = info["summary"]
        cat = s.get("by_category", {})
        row = (f"  {s['model']:<25} {s['overall_avg']:>7.3f} {s['pass_rate']:>6.1f}%  "
               f"{cat.get('ode', 0):>6.3f} {cat.get('analysis', 0):>6.3f} "
               f"{cat.get('analysis', 0):>6.3f} {cat.get('pde', 0):>6.3f} "
               f"{cat.get('optimization', 0):>6.3f}")
        print(row)

    print(f"\n  Report saved: {report_path}")
    return report


def show_report():
    """Display the most recent benchmark report."""
    reports = sorted(
        [f for f in os.listdir(REPORT_DIR) if f.endswith(".json")],
        reverse=True
    )
    if not reports:
        print("No reports found. Run: python benchmarks/run_mr.py")
        return
    path = os.path.join(REPORT_DIR, reports[0])
    with open(path, "r", encoding="utf-8") as f:
        report = json.load(f)
    print(json.dumps(report.get("summary", {}), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="MathReliability Benchmark")
    parser.add_argument("--model", help="Test a specific model")
    parser.add_argument("--models", help="Comma-separated model list")
    parser.add_argument("--quick", action="store_true", help="10-problem quick scan")
    parser.add_argument("--limit", type=int, default=0, help="Limit problems")
    parser.add_argument("--discover", action="store_true", help="Just list available models")
    parser.add_argument("--report-only", action="store_true", help="Show last report")
    args = parser.parse_args()

    if args.report_only:
        show_report()
        sys.exit(0)

    if args.discover:
        models = fetch_models()
        print(f"\nAvailable models at {API_BASE}:")
        for m in models:
            print(f"  - {m}")
        sys.exit(0)

    if args.model:
        models = [args.model]
    elif args.models:
        models = [m.strip() for m in args.models.split(",")]
    else:
        models = fetch_models()
        if not models:
            print("\nNo models discovered. Provide --model or set MATH_BENCH_API_KEY")
            print("Example: python benchmarks/run_mr.py --model qwen2.5-7b-instruct")
            sys.exit(1)

    run_benchmark(models, quick=args.quick, limit=args.limit)
