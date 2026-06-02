# Demo: Damped Harmonic Oscillator

**Math Agent Framework** in action: deriving, solving, and verifying a 2nd-order ODE.

![Demo](demo.gif)

## What This Shows

A complete mathematical workflow driven by the framework:

1. **Problem Statement** — 2nd order linear ODE with damping
2. **Classification** — SymPy classifies the ODE and selects solution method
3. **Symbolic Derivation** — characteristic equation, roots, general solution
4. **Numerical Verification** — checkodesol confirms zero residual, numerical evaluation
5. **5-Level Verification Pipeline** — SymPy → Monte Carlo → SageMath → Lean4 → QED
6. **Summary** — final verdict and one-command invocation

## Run It Yourself

```bash
pip install math-agent-framework
math-agent derive harmonic_oscillator
```

## Use This Demo

You're free to use `demo.gif` and `demo_output.json` in:
- Social media posts (X, LinkedIn, Reddit, Zhihu, V2EX)
- Presentations and talks
- Documentation and tutorials
- Any promotion of the Math Agent Framework

The demo shows the damped harmonic oscillator because it's:
- Visually meaningful (physics, engineering, mathematics)
- Shows classification → solving → verification
- Demonstrates the full pipeline in one clean example

## Files

| File | Description |
|------|-------------|
| `demo.gif` | Animated terminal-style walkthrough (6 frames) |
| `demo_output.json` | Full computational results |
| `generate_demo.py` | Script that produces this demo |
