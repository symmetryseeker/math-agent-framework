"""
Dynamic Difficulty Curve Generator — from existing benchmark reports.
====================================================================
Reads yesterday's MAF vs Raw benchmark results, extracts per-difficulty
and per-category breakdowns, and generates multi-model comparison plots.
"""
import json, os, sys
from collections import defaultdict
import numpy as np

REPORT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "reports")
RESULTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results")
os.makedirs(RESULTS_DIR, exist_ok=True)

# Load existing report
report_path = os.path.join(REPORT_DIR, "maf_vs_raw_20260603_174121.json")
with open(report_path, "r", encoding="utf-8") as f:
    data = json.load(f)

results = data["results"]
models = data["meta"]["models"]

# Extract per-difficulty and per-category stats
print("=" * 60)
print("  Extracting dynamic difficulty data...")
print("=" * 60)

difficulty_data = {}
category_data = {}
model_summaries = {}

for model_name, model_data in results.items():
    details = model_data.get("details", [])

    by_diff = defaultdict(lambda: {"raw": [], "maf": []})
    by_cat = defaultdict(lambda: {"raw": [], "maf": []})

    for d in details:
        level = d.get("difficulty", "unknown")
        cat = d.get("category", "unknown")
        by_diff[level]["raw"].append(d.get("raw_score", 0))
        by_diff[level]["maf"].append(d.get("maf_score", 0))
        by_cat[cat]["raw"].append(d.get("raw_score", 0))
        by_cat[cat]["maf"].append(d.get("maf_score", 0))

    # Summarize per level
    diff_summary = {}
    for level in sorted(by_diff.keys()):
        raw_scores = by_diff[level]["raw"]
        maf_scores = by_diff[level]["maf"]
        diff_summary[level] = {
            "n": len(raw_scores),
            "raw_accuracy": round(np.mean(raw_scores) * 100, 1),
            "maf_accuracy": round(np.mean(maf_scores) * 100, 1),
            "improvement": round((np.mean(maf_scores) - np.mean(raw_scores)) * 100, 1),
        }
        print(f"  {model_name:16s} {level:8s}: raw={diff_summary[level]['raw_accuracy']:5.1f}%  "
              f"maf={diff_summary[level]['maf_accuracy']:5.1f}%  "
              f"delta=+{diff_summary[level]['improvement']:5.1f}%  (n={diff_summary[level]['n']})")

    # Summarize per category
    cat_summary = {}
    for cat in sorted(by_cat.keys()):
        raw_scores = by_cat[cat]["raw"]
        maf_scores = by_cat[cat]["maf"]
        cat_summary[cat] = {
            "n": len(raw_scores),
            "raw_accuracy": round(np.mean(raw_scores) * 100, 1),
            "maf_accuracy": round(np.mean(maf_scores) * 100, 1),
            "improvement": round((np.mean(maf_scores) - np.mean(raw_scores)) * 100, 1),
        }
        print(f"  {model_name:16s} [{cat:12s}]: raw={cat_summary[cat]['raw_accuracy']:5.1f}%  "
              f"maf={cat_summary[cat]['maf_accuracy']:5.1f}%  "
              f"delta=+{cat_summary[cat]['improvement']:5.1f}%  (n={cat_summary[cat]['n']})")

    difficulty_data[model_name] = diff_summary
    category_data[model_name] = cat_summary
    model_summaries[model_name] = {
        "raw_accuracy": model_data["raw_accuracy"] * 100,
        "maf_accuracy": model_data["maf_accuracy"] * 100,
    }

print()
print(f"  Data extracted for {len(models)} models across {len(difficulty_data[models[0]])} levels")

# ============================================================
# Generate Dynamic Difficulty Curves
# ============================================================
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

THEME = {
    'bg': '#1e1e2e', 'fg': '#cdd6f4',
    'raw': '#f38ba8', 'maf': '#a6e3a1',
    'grid': '#45475a', 'text': '#bac2de',
    'models': {'qwen3-8b': '#89b4fa', 'qwen3-32b': '#cba6f7', 'DeepSeek-V3.2': '#fab387'},
}

# --- Plot 1: Per-Model Difficulty Curve (3 subplots) ---
fig, axes = plt.subplots(1, 3, figsize=(18, 5.5))
fig.patch.set_facecolor(THEME['bg'])

for ax_idx, model_name in enumerate(models):
    ax = axes[ax_idx]
    ax.set_facecolor(THEME['bg'])

    dd = difficulty_data[model_name]
    levels = sorted(dd.keys())
    x = np.arange(len(levels))
    width = 0.32

    raw_vals = [dd[l]["raw_accuracy"] for l in levels]
    maf_vals = [dd[l]["maf_accuracy"] for l in levels]

    bars1 = ax.bar(x - width/2, raw_vals, width, label='Raw (no tools)',
                   color=THEME['raw'], alpha=0.85, edgecolor='white', linewidth=0.3)
    bars2 = ax.bar(x + width/2, maf_vals, width, label='MAF (with tools)',
                   color=THEME['maf'], alpha=0.85, edgecolor='white', linewidth=0.3)

    for bar in bars1:
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 2,
               f'{bar.get_height():.0f}%', ha='center', fontsize=8,
               color=THEME['raw'], fontweight='bold')
    for bar in bars2:
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 2,
               f'{bar.get_height():.0f}%', ha='center', fontsize=8,
               color=THEME['maf'], fontweight='bold')

    ax.set_xticks(x)
    ax.set_xticklabels([l.capitalize() for l in levels], fontsize=10, color=THEME['text'])
    ax.set_ylim(0, 115)
    ax.set_title(f'{model_name}', color=THEME['fg'], fontsize=12, fontweight='bold')
    ax.legend(fontsize=8, facecolor='#313244', edgecolor=THEME['grid'], labelcolor=THEME['text'])
    ax.grid(True, alpha=0.12, color=THEME['text'], axis='y')
    ax.tick_params(colors=THEME['text'], labelsize=9)
    for spine in ax.spines.values():
        spine.set_color(THEME['grid'])

    # Summary box
    s = model_summaries[model_name]
    ax.text(0.98, 0.95, f'Overall: {s["raw_accuracy"]:.0f}% -> {s["maf_accuracy"]:.0f}%',
           transform=ax.transAxes, fontsize=9, color=THEME['fg'], ha='right',
           bbox=dict(boxstyle='round,pad=0.3', facecolor='#313244', edgecolor=THEME['grid'], alpha=0.8))

fig.suptitle('Dynamic Difficulty Curve — Raw LLM vs MAF (Math Agent Framework)',
             color=THEME['fg'], fontsize=14, fontweight='bold', y=1.02)
fig.tight_layout()
curve1_path = os.path.join(RESULTS_DIR, "difficulty_by_model.png")
fig.savefig(curve1_path, dpi=150, bbox_inches='tight', facecolor=THEME['bg'])
plt.close(fig)
print(f"  Saved: {curve1_path}")

# --- Plot 2: Per-Category Breakdown (side-by-side for all models) ---
all_cats = sorted(set().union(*[category_data[m].keys() for m in models]))
fig2, axes2 = plt.subplots(1, len(all_cats), figsize=(5*len(all_cats), 5))
fig2.patch.set_facecolor(THEME['bg'])

for ax_idx, cat in enumerate(all_cats):
    ax = axes2[ax_idx] if len(all_cats) > 1 else axes2
    ax.set_facecolor(THEME['bg'])

    x = np.arange(len(models))
    width = 0.28

    for i, model_name in enumerate(models):
        cd = category_data[model_name].get(cat, {"raw_accuracy": 0, "maf_accuracy": 0})
        ax.bar(i - width/2, cd["raw_accuracy"], width, color=THEME['raw'], alpha=0.85,
               edgecolor='white', linewidth=0.3)
        ax.bar(i + width/2, cd["maf_accuracy"], width, color=THEME['maf'], alpha=0.85,
               edgecolor='white', linewidth=0.3)

    ax.set_xticks(x)
    ax.set_xticklabels(models, fontsize=9, color=THEME['text'], rotation=15)
    ax.set_ylim(0, 115)
    ax.set_title(f'{cat.upper()}', color=THEME['fg'], fontsize=11, fontweight='bold')
    ax.grid(True, alpha=0.12, color=THEME['text'], axis='y')
    ax.tick_params(colors=THEME['text'], labelsize=8)
    for spine in ax.spines.values():
        spine.set_color(THEME['grid'])

# Legend
from matplotlib.patches import Patch
legend_elements = [
    Patch(facecolor=THEME['raw'], alpha=0.85, label='Raw LLM (no tools)'),
    Patch(facecolor=THEME['maf'], alpha=0.85, label='MAF (with tools)'),
]
fig2.legend(handles=legend_elements, loc='upper center', ncol=2, fontsize=10,
            facecolor='#313244', edgecolor=THEME['grid'], labelcolor=THEME['text'])
fig2.suptitle('Per-Category Accuracy: Raw vs MAF',
              color=THEME['fg'], fontsize=14, fontweight='bold', y=1.05)
fig2.tight_layout()
curve2_path = os.path.join(RESULTS_DIR, "difficulty_by_category.png")
fig2.savefig(curve2_path, dpi=150, bbox_inches='tight', facecolor=THEME['bg'])
plt.close(fig2)
print(f"  Saved: {curve2_path}")

# --- Plot 3: Gap Analysis — improvement by difficulty ---
fig3, ax3 = plt.subplots(figsize=(10, 5))
fig3.patch.set_facecolor(THEME['bg'])
ax3.set_facecolor(THEME['bg'])

levels_all = sorted(difficulty_data[models[0]].keys())
x3 = np.arange(len(levels_all))
width3 = 0.25

for i, model_name in enumerate(models):
    improvements = [difficulty_data[model_name][l]["improvement"] for l in levels_all]
    ax3.bar(x3 + (i-1)*width3, improvements, width3,
           color=THEME['models'].get(model_name, THEME['text']),
           alpha=0.9, edgecolor='white', linewidth=0.3, label=model_name)
    for j, imp in enumerate(improvements):
        ax3.text(x3[j] + (i-1)*width3, imp + 1, f'+{imp:.0f}%', ha='center',
                fontsize=8, color=THEME['fg'], fontweight='bold')

ax3.set_xticks(x3)
ax3.set_xticklabels([l.capitalize() for l in levels_all], fontsize=11, color=THEME['text'])
ax3.set_ylabel('MAF Improvement (pp)', color=THEME['text'], fontsize=11)
ax3.set_title('Absolute Improvement by Difficulty Level', color=THEME['fg'],
              fontsize=13, fontweight='bold')
ax3.legend(fontsize=9, facecolor='#313244', edgecolor=THEME['grid'], labelcolor=THEME['text'])
ax3.grid(True, alpha=0.12, color=THEME['text'], axis='y')
ax3.tick_params(colors=THEME['text'], labelsize=10)
for spine in ax3.spines.values():
    spine.set_color(THEME['grid'])

fig3.tight_layout()
curve3_path = os.path.join(RESULTS_DIR, "difficulty_gap_analysis.png")
fig3.savefig(curve3_path, dpi=150, bbox_inches='tight', facecolor=THEME['bg'])
plt.close(fig3)
print(f"  Saved: {curve3_path}")

print(f"\n{'='*60}")
print(f"  Dynamic difficulty curves complete")
print(f"  Results: {RESULTS_DIR}")
print(f"{'='*60}")
