"""Generate final comparison bar chart."""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

T = {'bg': '#1e1e2e', 'fg': '#cdd6f4', 'text': '#bac2de', 'grid': '#45475a',
     'raw': '#f38ba8', 'mcp': '#fab387', 'maf': '#a6e3a1'}

data = {
    'qwen3-8b':    [22, 44, 44],
    'qwen3-32b':   [33, 33, 44],
    'DeepSeek-V3.2': [78, 89, 100],
}
models = list(data.keys())
tiers = ['Raw LLM', 'Raw MCP', 'MAF (Harness+MCP)']
tier_colors = [T['raw'], T['mcp'], T['maf']]

fig, ax = plt.subplots(figsize=(12, 6))
fig.patch.set_facecolor(T['bg'])
ax.set_facecolor(T['bg'])

x = np.arange(len(models))
width = 0.22

for i, (tier, color) in enumerate(zip(tiers, tier_colors)):
    vals = [data[m][i] for m in models]
    bars = ax.bar(x + (i-1)*width, vals, width, label=tier, color=color,
                  alpha=0.9, edgecolor='white', linewidth=0.5)
    for bar, val in zip(bars, vals):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 2,
                f'{val}%', ha='center', fontsize=10, color=T['fg'], fontweight='bold')

ax.set_xticks(x)
ax.set_xticklabels(models, fontsize=12, color=T['text'])
ax.set_ylabel('Accuracy (%)', color=T['text'], fontsize=12)
ax.set_ylim(0, 115)
ax.set_title('Math Agent Framework — Final Benchmark\nRaw LLM vs Raw MCP vs MAF (Harness + MCP)',
             color=T['fg'], fontsize=14, fontweight='bold')
ax.legend(fontsize=11, facecolor='#313244', edgecolor=T['grid'], labelcolor=T['text'])
ax.grid(True, alpha=0.12, color=T['text'], axis='y')
ax.tick_params(colors=T['text'], labelsize=11)
for spine in ax.spines.values():
    spine.set_color(T['grid'])

# Insight annotations
ax.annotate('+22pp', xy=(0, 44), xytext=(0.8, 65),
            arrowprops=dict(arrowstyle='->', color=T['maf'], lw=1.5),
            fontsize=9, color=T['maf'], fontweight='bold')
ax.annotate('+22pp', xy=(2, 100), xytext=(2.5, 108),
            arrowprops=dict(arrowstyle='->', color=T['maf'], lw=1.5),
            fontsize=9, color=T['maf'], fontweight='bold')

fig.tight_layout()
path = 'benchmarks/results/final_comparison.png'
fig.savefig(path, dpi=150, bbox_inches='tight', facecolor=T['bg'])
plt.close(fig)
print(f'Saved: {path}')
