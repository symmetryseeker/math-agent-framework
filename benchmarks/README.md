# MathReliability Benchmark v1

Tests LLM models on mathematical reliability across 5 dimensions.

## Quick Start

```bash
# Set your API key (BIT MAAS platform)
export MATH_BENCH_API_KEY="your-api-key"
export MATH_BENCH_BASE_URL="https://maas.bit.edu.cn/v1-openai"

# Discover available models
python benchmarks/run_mr.py --discover

# Quick scan (10 problems, ~2 min)
python benchmarks/run_mr.py --quick

# Full benchmark (50 problems, ~10 min)
python benchmarks/run_mr.py

# Test specific model
python benchmarks/run_mr.py --model qwen2.5-7b-instruct

# Test multiple models
python benchmarks/run_mr.py --models qwen2.5-7b,qwen2.5-14b,qwen2.5-32b

# Show last report
python benchmarks/run_mr.py --report-only
```

## Scoring

Each problem scored on 4 dimensions (weighted):

| Dimension | Weight | What it measures |
|-----------|--------|-----------------|
| Classification | 25% | Did the LLM identify the right problem type? |
| Tool Selection | 30% | Did it name appropriate tools? |
| Correctness | 30% | Does the answer match the expected result? |
| Verification Awareness | 15% | Did it recognize the need for verification? |

## Problem Categories (50 total)

| Category | Count | Difficulty |
|----------|-------|-----------|
| ODE | 10 | 3 easy, 5 medium, 2 hard |
| Limits | 10 | 4 easy, 4 medium, 2 hard |
| Series | 5 | 2 easy, 2 medium, 1 hard |
| Integrals | 5 | 2 easy, 3 medium |
| PDE | 5 | 3 easy, 2 medium |
| Optimization | 5 | 2 easy, 2 medium, 1 hard |
| Special Functions | 5 | 2 easy, 2 medium, 1 hard |
| Physics | 5 | 2 easy, 2 medium, 1 hard |

## Output

Reports saved to `benchmarks/reports/mr_report_YYYYMMDD_HHMMSS.json`
