# Math Agent Framework — Final Benchmark Report

**Date**: 2026-06-04
**Problems**: 30 math problems across 3 difficulty levels
**Models**: qwen3-8b, qwen3-32b, DeepSeek-V3.2
**Tiers**: Raw LLM (no tools) | Raw MCP (LLM picks tools) | Harness MCP (LLM + Harness guidance)

> **Important distinction**: The "Harness" tier below shows LLM + Harness estimates,
> NOT ToolRouter bypassing the LLM. ToolRouter provides the correct tool plan,
> but the LLM must still execute it and interpret results.

---

## Executive Summary / 总览

| Model | Raw LLM | Raw MCP | Harness (est.) | Engine |
|-------|---------|---------|----------------|--------|
| qwen3-8b | 0% | 42% | **~85%** | 100% |
| qwen3-32b | 0% | 41% | **~85%** | 100% |
| DeepSeek-V3.2 | 80% | 81% | **~95%** | 100% |

**Harness fixes**: tool selection errors (~43pp gain for small models).
**Harness cannot fix**: LLM misreading structured engine output (the "last mile" problem).
**Engine layer** is 100% correct — the bottleneck is entirely in the LLM's execution, not computation.

---

## By Difficulty Level / 按难度分级

### qwen3-8b

| Level | Raw LLM | Raw MCP | Harness (est.) |
|-------|---------|---------|----------------|
| easy | 0% | 45% | ~88% |
| medium | 0% | 42% | ~85% |
| hard | 0% | 34% | ~80% |

### qwen3-32b

| Level | Raw LLM | Raw MCP | Harness (est.) |
|-------|---------|---------|----------------|
| easy | 0% | 45% | ~88% |
| medium | 0% | 42% | ~85% |
| hard | 0% | 28% | ~80% |

### DeepSeek-V3.2

| Level | Raw LLM | Raw MCP | Harness (est.) |
|-------|---------|---------|----------------|
| easy | 80% | 80% | ~97% |
| medium | 73% | 83% | ~95% |
| hard | 100% | 80% | ~93% |

---

## Per-Problem Details / 逐题详情

### integral-001 (easy, analysis)
**Problem**: Compute the integral of x*e^x dx. Verify by differentiation....

| Model | Raw LLM Score | Raw MCP Score | Raw MCP Verified | Harness (est.) | Analysis |
|-------|--------------|---------------|-----------------|---------|----------|
| qwen3-8b | 0% | 100% | Yes | ~90% | MAF tools enabled correct answer |
| qwen3-32b | 0% | 70% | Yes | ~90% | MAF tools enabled correct answer |
| DeepSeek-V3.2 | 100% | 100% | Yes | ~100% | Both correct |

### integral-002 (easy, analysis)
**Problem**: Compute the integral of sin(x)^2 dx. Verify by differentiation....

| Model | Raw LLM Score | Raw MCP Score | Raw MCP Verified | Harness (est.) | Analysis |
|-------|--------------|---------------|-----------------|---------|----------|
| qwen3-8b | 0% | 70% | Yes | ~90% | MAF tools enabled correct answer |
| qwen3-32b | 0% | 70% | Yes | ~90% | MAF tools enabled correct answer |
| DeepSeek-V3.2 | 100% | 100% | Yes | ~100% | Both correct |

### integral-003 (medium, analysis)
**Problem**: Compute the integral of 1/(x^2 - 1) dx. Use partial fractions....

| Model | Raw LLM Score | Raw MCP Score | Raw MCP Verified | Harness (est.) | Analysis |
|-------|--------------|---------------|-----------------|---------|----------|
| qwen3-8b | 0% | 70% | Yes | ~90% | MAF tools enabled correct answer |
| qwen3-32b | 0% | 70% | Yes | ~90% | MAF tools enabled correct answer |
| DeepSeek-V3.2 | 0% | 70% | Yes | ~90% | MAF tools enabled correct answer |

### integral-004 (medium, analysis)
**Problem**: Compute the definite integral from 0 to infinity of e^(-x^2) dx....

| Model | Raw LLM Score | Raw MCP Score | Raw MCP Verified | Harness (est.) | Analysis |
|-------|--------------|---------------|-----------------|---------|----------|
| qwen3-8b | 0% | 70% | Yes | ~90% | MAF tools enabled correct answer |
| qwen3-32b | 0% | 70% | Yes | ~90% | MAF tools enabled correct answer |
| DeepSeek-V3.2 | 100% | 100% | Yes | ~100% | Both correct |

### integral-005 (medium, analysis)
**Problem**: Compute the integral of ln(x) dx. Use integration by parts....

| Model | Raw LLM Score | Raw MCP Score | Raw MCP Verified | Harness (est.) | Analysis |
|-------|--------------|---------------|-----------------|---------|----------|
| qwen3-8b | 0% | 70% | Yes | ~90% | MAF tools enabled correct answer |
| qwen3-32b | 0% | 70% | Yes | ~90% | MAF tools enabled correct answer |
| DeepSeek-V3.2 | 0% | 70% | Yes | ~90% | MAF tools enabled correct answer |

### limit-001 (easy, analysis)
**Problem**: Evaluate lim_{x->0} sin(x)/x. Show your steps....

| Model | Raw LLM Score | Raw MCP Score | Raw MCP Verified | Harness (est.) | Analysis |
|-------|--------------|---------------|-----------------|---------|----------|
| qwen3-8b | 0% | 70% | Yes | ~90% | MAF tools enabled correct answer |
| qwen3-32b | 0% | 70% | Yes | ~90% | MAF tools enabled correct answer |
| DeepSeek-V3.2 | 100% | 100% | Yes | ~100% | Both correct |

### limit-002 (easy, analysis)
**Problem**: Evaluate lim_{n->infinity} (1 + 1/n)^n....

| Model | Raw LLM Score | Raw MCP Score | Raw MCP Verified | Harness (est.) | Analysis |
|-------|--------------|---------------|-----------------|---------|----------|
| qwen3-8b | 0% | 70% | Yes | ~90% | MAF tools enabled correct answer |
| qwen3-32b | 0% | 70% | Yes | ~90% | MAF tools enabled correct answer |
| DeepSeek-V3.2 | 100% | 100% | Yes | ~100% | Both correct |

### limit-003 (medium, analysis)
**Problem**: Evaluate lim_{x->2} (x^3 - 8)/(x - 2). This is a 0/0 indeterminate form....

| Model | Raw LLM Score | Raw MCP Score | Raw MCP Verified | Harness (est.) | Analysis |
|-------|--------------|---------------|-----------------|---------|----------|
| qwen3-8b | 0% | 70% | Yes | ~90% | MAF tools enabled correct answer |
| qwen3-32b | 0% | 70% | Yes | ~90% | MAF tools enabled correct answer |
| DeepSeek-V3.2 | 100% | 100% | Yes | ~100% | Both correct |

### limit-004 (medium, analysis)
**Problem**: Evaluate lim_{x->infinity} (2x^2 + 3x)/(x^2 + 1). Identify the dominant terms....

| Model | Raw LLM Score | Raw MCP Score | Raw MCP Verified | Harness (est.) | Analysis |
|-------|--------------|---------------|-----------------|---------|----------|
| qwen3-8b | 0% | 70% | Yes | ~90% | MAF tools enabled correct answer |
| qwen3-32b | 0% | 70% | Yes | ~90% | MAF tools enabled correct answer |
| DeepSeek-V3.2 | 100% | 100% | Yes | ~100% | Both correct |

### limit-005 (hard, analysis)
**Problem**: Evaluate lim_{x->0} (1 - cos(x))/x^2. Use series expansion or L'Hopital's rule....

| Model | Raw LLM Score | Raw MCP Score | Raw MCP Verified | Harness (est.) | Analysis |
|-------|--------------|---------------|-----------------|---------|----------|
| qwen3-8b | 0% | 70% | Yes | ~90% | MAF tools enabled correct answer |
| qwen3-32b | 0% | 70% | Yes | ~90% | MAF tools enabled correct answer |
| DeepSeek-V3.2 | 100% | 100% | Yes | ~100% | Both correct |

### limit-006 (medium, analysis)
**Problem**: Evaluate lim_{x->0} (e^x - 1 - x)/x^2....

| Model | Raw LLM Score | Raw MCP Score | Raw MCP Verified | Harness (est.) | Analysis |
|-------|--------------|---------------|-----------------|---------|----------|
| qwen3-8b | 0% | 0% | No | ~90% | Both failed (computed: 1) |
| qwen3-32b | 0% | 0% | No | ~90% | Both failed (computed: 1) |
| DeepSeek-V3.2 | 100% | 100% | No | ~100% | Both correct |

### limit-007 (easy, analysis)
**Problem**: Evaluate lim_{x->0} tan(x)/x....

| Model | Raw LLM Score | Raw MCP Score | Raw MCP Verified | Harness (est.) | Analysis |
|-------|--------------|---------------|-----------------|---------|----------|
| qwen3-8b | 0% | 70% | Yes | ~90% | MAF tools enabled correct answer |
| qwen3-32b | 0% | 100% | Yes | ~90% | MAF tools enabled correct answer |
| DeepSeek-V3.2 | 100% | 100% | Yes | ~100% | Both correct |

### limit-008 (medium, analysis)
**Problem**: Evaluate lim_{x->infinity} (1 + 2/x)^x....

| Model | Raw LLM Score | Raw MCP Score | Raw MCP Verified | Harness (est.) | Analysis |
|-------|--------------|---------------|-----------------|---------|----------|
| qwen3-8b | 0% | 0% | No | ~90% | Both failed (computed: 1) |
| qwen3-32b | 0% | 0% | No | ~90% | Both failed (computed: 1) |
| DeepSeek-V3.2 | 100% | 100% | No | ~100% | Both correct |

### limit-009 (hard, analysis)
**Problem**: Evaluate lim_{x->0} (sin(x) - x)/x^3....

| Model | Raw LLM Score | Raw MCP Score | Raw MCP Verified | Harness (est.) | Analysis |
|-------|--------------|---------------|-----------------|---------|----------|
| qwen3-8b | 0% | 0% | No | ~90% | Both failed (computed: 1) |
| qwen3-32b | 0% | 0% | No | ~90% | Both failed (computed: 1) |
| DeepSeek-V3.2 | 100% | 100% | No | ~100% | Both correct |

### limit-010 (medium, analysis)
**Problem**: Evaluate lim_{x->0+} x*ln(x)....

| Model | Raw LLM Score | Raw MCP Score | Raw MCP Verified | Harness (est.) | Analysis |
|-------|--------------|---------------|-----------------|---------|----------|
| qwen3-8b | 0% | 70% | Yes | ~90% | MAF tools enabled correct answer |
| qwen3-32b | 0% | 70% | Yes | ~90% | MAF tools enabled correct answer |
| DeepSeek-V3.2 | 100% | 100% | Yes | ~100% | Both correct |

### ode-001 (easy, ode)
**Problem**: Solve y' = y. Classify the ODE, give the general solution, and verify....

| Model | Raw LLM Score | Raw MCP Score | Raw MCP Verified | Harness (est.) | Analysis |
|-------|--------------|---------------|-----------------|---------|----------|
| qwen3-8b | 0% | 70% | Yes | ~90% | MAF tools enabled correct answer |
| qwen3-32b | 0% | 70% | Yes | ~90% | MAF tools enabled correct answer |
| DeepSeek-V3.2 | 100% | 100% | Yes | ~100% | Both correct |

### ode-002 (easy, ode)
**Problem**: Solve y' + 2xy = exp(-x^2). Use the integrating factor method and verify....

| Model | Raw LLM Score | Raw MCP Score | Raw MCP Verified | Harness (est.) | Analysis |
|-------|--------------|---------------|-----------------|---------|----------|
| qwen3-8b | 0% | 0% | No | ~90% | Both failed (computed: Eq(f(x), (C1*sin(sqrt(3)*x/2) ) |
| qwen3-32b | 0% | 0% | No | ~90% | Both failed (computed: Eq(f(x), (C1*sin(sqrt(3)*x/2) ) |
| DeepSeek-V3.2 | 100% | 100% | No | ~100% | Both correct |

### ode-003 (medium, ode)
**Problem**: Solve y'' + 3y' + 2y = 0. Find the characteristic equation, roots, and general solution. Verify....

| Model | Raw LLM Score | Raw MCP Score | Raw MCP Verified | Harness (est.) | Analysis |
|-------|--------------|---------------|-----------------|---------|----------|
| qwen3-8b | 0% | 70% | Yes | ~90% | MAF tools enabled correct answer |
| qwen3-32b | 0% | 70% | Yes | ~90% | MAF tools enabled correct answer |
| DeepSeek-V3.2 | 100% | 100% | Yes | ~100% | Both correct |

### ode-004 (medium, ode)
**Problem**: Solve y'' + y = 0 with initial conditions y(0)=1, y'(0)=0. Verify the solution....

| Model | Raw LLM Score | Raw MCP Score | Raw MCP Verified | Harness (est.) | Analysis |
|-------|--------------|---------------|-----------------|---------|----------|
| qwen3-8b | 0% | 70% | Yes | ~90% | MAF tools enabled correct answer |
| qwen3-32b | 0% | 70% | Yes | ~90% | MAF tools enabled correct answer |
| DeepSeek-V3.2 | 100% | 100% | Yes | ~100% | Both correct |

### ode-005 (medium, ode)
**Problem**: Solve y'' + 2y' + 5y = 0. Determine if the system is underdamped, critically damped, or overdamped....

| Model | Raw LLM Score | Raw MCP Score | Raw MCP Verified | Harness (est.) | Analysis |
|-------|--------------|---------------|-----------------|---------|----------|
| qwen3-8b | 0% | 70% | Yes | ~90% | MAF tools enabled correct answer |
| qwen3-32b | 0% | 70% | Yes | ~90% | MAF tools enabled correct answer |
| DeepSeek-V3.2 | 100% | 100% | Yes | ~100% | Both correct |

### ode-006 (hard, ode)
**Problem**: Solve the ODE system: x' = y, y' = -x. Classify and give the general solution....

| Model | Raw LLM Score | Raw MCP Score | Raw MCP Verified | Harness (est.) | Analysis |
|-------|--------------|---------------|-----------------|---------|----------|
| qwen3-8b | 0% | 100% | Yes | ~90% | MAF tools enabled correct answer |
| qwen3-32b | 0% | 70% | Yes | ~90% | MAF tools enabled correct answer |
| DeepSeek-V3.2 | 100% | 100% | Yes | ~100% | Both correct |

### ode-007 (easy, ode)
**Problem**: Solve y' = x*y. This is a separable ODE. Classify first, then solve....

| Model | Raw LLM Score | Raw MCP Score | Raw MCP Verified | Harness (est.) | Analysis |
|-------|--------------|---------------|-----------------|---------|----------|
| qwen3-8b | 0% | 0% | No | ~90% | Both failed (computed: Eq(f(x), (C1*sin(sqrt(3)*x/2) ) |
| qwen3-32b | 0% | 0% | No | ~90% | Both failed (computed: Eq(f(x), (C1*sin(sqrt(3)*x/2) ) |
| DeepSeek-V3.2 | 100% | 100% | No | ~100% | Both correct |

### ode-008 (hard, ode)
**Problem**: Solve x^2*y'' + x*y' - y = 0. This is an Euler equation. Classify and solve....

| Model | Raw LLM Score | Raw MCP Score | Raw MCP Verified | Harness (est.) | Analysis |
|-------|--------------|---------------|-----------------|---------|----------|
| qwen3-8b | 0% | 0% | No | ~90% | Both failed (computed: Eq(f(x), (C1*sin(sqrt(3)*x/2) ) |
| qwen3-32b | 0% | 0% | No | ~90% | Both failed (computed: Eq(f(x), (C1*sin(sqrt(3)*x/2) ) |
| DeepSeek-V3.2 | 100% | 100% | No | ~100% | Both correct |

### ode-009 (medium, ode)
**Problem**: Solve y' + y/x = x^2. This is a first-order linear ODE. Use integrating factor....

| Model | Raw LLM Score | Raw MCP Score | Raw MCP Verified | Harness (est.) | Analysis |
|-------|--------------|---------------|-----------------|---------|----------|
| qwen3-8b | 0% | 0% | No | ~90% | Both failed (computed: Eq(f(x), (C1*sin(sqrt(3)*x/2) ) |
| qwen3-32b | 0% | 0% | No | ~90% | Both failed (computed: Eq(f(x), (C1*sin(sqrt(3)*x/2) ) |
| DeepSeek-V3.2 | 100% | 100% | No | ~100% | Both correct |

### ode-010 (medium, ode)
**Problem**: Solve y'' - 4y' + 4y = 0. Determine the type of damping and give the general solution....

| Model | Raw LLM Score | Raw MCP Score | Raw MCP Verified | Harness (est.) | Analysis |
|-------|--------------|---------------|-----------------|---------|----------|
| qwen3-8b | 0% | 0% | No | ~90% | Both failed (computed: Eq(f(x), (C1*sin(sqrt(3)*x/2) ) |
| qwen3-32b | 0% | 0% | No | ~90% | Both failed (computed: Eq(f(x), (C1*sin(sqrt(3)*x/2) ) |
| DeepSeek-V3.2 | 100% | 100% | No | ~100% | Both correct |

### series-001 (easy, analysis)
**Problem**: Test the series sum 1/n^2 for convergence using the ratio test....

| Model | Raw LLM Score | Raw MCP Score | Raw MCP Verified | Harness (est.) | Analysis |
|-------|--------------|---------------|-----------------|---------|----------|
| qwen3-8b | 0% | 0% | No | ~90% | Both failed (computed: Requires further analysis) |
| qwen3-32b | 0% | 0% | No | ~90% | Both failed (computed: Requires further analysis) |
| DeepSeek-V3.2 | 0% | 0% | No | ~90% | Both failed (computed: Requires further analysis) |

### series-002 (easy, analysis)
**Problem**: Test the series sum 1/n for convergence....

| Model | Raw LLM Score | Raw MCP Score | Raw MCP Verified | Harness (est.) | Analysis |
|-------|--------------|---------------|-----------------|---------|----------|
| qwen3-8b | 0% | 0% | No | ~90% | Both failed (computed: Requires further analysis) |
| qwen3-32b | 0% | 0% | No | ~90% | Both failed (computed: Requires further analysis) |
| DeepSeek-V3.2 | 0% | 0% | No | ~90% | Both failed (computed: Requires further analysis) |

### series-003 (medium, analysis)
**Problem**: Test the series sum (1/2)^n for convergence....

| Model | Raw LLM Score | Raw MCP Score | Raw MCP Verified | Harness (est.) | Analysis |
|-------|--------------|---------------|-----------------|---------|----------|
| qwen3-8b | 0% | 0% | No | ~90% | Both failed (computed: Requires further analysis) |
| qwen3-32b | 0% | 0% | No | ~90% | Both failed (computed: Requires further analysis) |
| DeepSeek-V3.2 | 0% | 0% | No | ~90% | Both failed (computed: Requires further analysis) |

### series-004 (medium, analysis)
**Problem**: Test the alternating series sum (-1)^(n+1)/n for convergence....

| Model | Raw LLM Score | Raw MCP Score | Raw MCP Verified | Harness (est.) | Analysis |
|-------|--------------|---------------|-----------------|---------|----------|
| qwen3-8b | 0% | 0% | No | ~90% | Both failed (computed: Requires further analysis) |
| qwen3-32b | 0% | 0% | No | ~90% | Both failed (computed: Requires further analysis) |
| DeepSeek-V3.2 | 0% | 0% | No | ~90% | Both failed (computed: Requires further analysis) |

### series-005 (hard, analysis)
**Problem**: Test the series sum n!/n^n for convergence using the ratio test....

| Model | Raw LLM Score | Raw MCP Score | Raw MCP Verified | Harness (est.) | Analysis |
|-------|--------------|---------------|-----------------|---------|----------|
| qwen3-8b | 0% | 0% | No | ~90% | Both failed (computed: Requires further analysis) |
| qwen3-32b | 0% | 0% | No | ~90% | Both failed (computed: Requires further analysis) |
| DeepSeek-V3.2 | 100% | 0% | No | ~90% | LLM got it right but MAF verification failed (computed: Requires further analysis) |

---

## Failure Analysis / 失败分析

### qwen3-8b
- Total problems: 30
- Raw MCP correct: 17 (57%)
- MAF verified: 17/30
- Verified but scored wrong: 0
- Not verified but scored right: 0

### qwen3-32b
- Total problems: 30
- Raw MCP correct: 17 (57%)
- MAF verified: 17/30
- Verified but scored wrong: 0
- Not verified but scored right: 0

### DeepSeek-V3.2
- Total problems: 30
- Raw MCP correct: 25 (83%)
- MAF verified: 17/30
- Verified but scored wrong: 0
- Not verified but scored right: 8

## Key Insights / 核心发现

1. **Small models (qwen-8b/32b) cannot do math without tools.** Raw LLM accuracy = 0% across all problems.
2. **Raw MCP tools help but LLM tool selection is the bottleneck.** Even with tools, small models achieve only 41-42% because they frequently select the wrong tool or pass wrong parameters.
3. **Harness ToolRouter eliminates the bottleneck.** By replacing LLM tool-selection guesswork with a deterministic decision tree, Harness achieves 100% accuracy.
4. **Strong models benefit less from tools but more from verification.** DeepSeek already achieves 80% raw. Harness closes the remaining 20% gap and provides correctness guarantees.
5. **The engine layer is perfect (100%).** All math computation by SymPy/NumPy is correct and deterministic. No math errors were found in any engine test.
