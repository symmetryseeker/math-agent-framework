"""
Generate advanced demo images for Feishu documentation.
Shows: ODE regimes, PDE heat equation, verification pipeline, architecture diagram.
"""
import sys, io, os
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import matplotlib.patches as mpatches

DEMO_DIR = os.path.dirname(os.path.abspath(__file__))
THEME = {
    'bg': '#1e1e2e', 'fg': '#cdd6f4', 'accent1': '#89b4fa', 'accent2': '#a6e3a1',
    'accent3': '#f38ba8', 'accent4': '#fab387', 'accent5': '#cba6f7',
    'grid': '#45475a', 'text': '#bac2de',
}
plt.rcParams.update({'text.color': THEME['text'], 'axes.edgecolor': THEME['grid']})

# ============================================================
# Figure 1: Multi-domain Overview (2x2 grid: ODE, PDE, Analysis, Verification)
# ============================================================
fig, axes = plt.subplots(2, 2, figsize=(14, 10))
fig.patch.set_facecolor(THEME['bg'])

# --- ODE: Damped oscillator ---
ax = axes[0, 0]
ax.set_facecolor(THEME['bg'])
t = np.linspace(0, 8, 200)
for beta, color, label in [(0.3, THEME['accent1'], 'Underdamped'),
                             (2.0, THEME['accent2'], 'Critical'),
                             (4.0, THEME['accent3'], 'Overdamped')]:
    w_d = np.sqrt(max(4 - beta**2, 0))
    if beta < 2:
        x = np.exp(-beta*t) * np.cos(w_d*t)
    elif abs(beta-2) < 1e-6:
        x = np.exp(-2*t) * (1 + 2*t)
    else:
        r1, r2 = -beta + np.sqrt(beta**2-4), -beta - np.sqrt(beta**2-4)
        x = (r2*np.exp(r1*t) - r1*np.exp(r2*t)) / (r2 - r1)
    ax.plot(t, x, color=color, linewidth=1.8, label=label)
ax.axhline(y=0, color=THEME['grid'], linewidth=0.5)
ax.set_title('ODE: Damped Harmonic Oscillator', color=THEME['fg'], fontweight='bold', fontsize=11)
ax.legend(fontsize=8, facecolor='#313244', edgecolor=THEME['grid'], labelcolor=THEME['text'])
ax.grid(True, alpha=0.15, color=THEME['text'])
ax.tick_params(colors=THEME['text'], labelsize=8)
for spine in ax.spines.values(): spine.set_color(THEME['grid'])

# --- PDE: Heat Equation ---
ax = axes[0, 1]
ax.set_facecolor(THEME['bg'])
nx, nt = 40, 80
u = np.zeros((nt, nx))
u[0, nx//4:3*nx//4] = 1.0
alpha, dx, dt = 0.2, 1.0/(nx-1), 0.5/nt
r = alpha*dt/dx**2
for n in range(nt-1):
    u[n+1, 1:-1] = u[n, 1:-1] + r*(u[n, 2:] - 2*u[n, 1:-1] + u[n, :-2])
    u[n+1, 0] = u[n+1, -1] = 0
im = ax.imshow(u, aspect='auto', cmap='plasma', origin='lower',
               extent=[0, 1, 0, 0.5], interpolation='bilinear')
ax.set_title('PDE: 1D Heat Equation  u_t = 0.2 u_xx', color=THEME['fg'], fontweight='bold', fontsize=11)
ax.set_xlabel('x', color=THEME['text'], fontsize=9)
ax.set_ylabel('t', color=THEME['text'], fontsize=9)
ax.tick_params(colors=THEME['text'], labelsize=8)
plt.colorbar(im, ax=ax, label='u(x,t)').set_label('u(x,t)', color=THEME['text'])
for spine in ax.spines.values(): spine.set_color(THEME['grid'])

# --- Analysis: Limit + Series ---
ax = axes[1, 0]
ax.set_facecolor(THEME['bg'])
x_vals = np.logspace(-3, 0.5, 100)
ax.semilogx(x_vals, np.sin(x_vals)/x_vals, color=THEME['accent1'], linewidth=2, label='sin(x)/x')
ax.axhline(y=1, color=THEME['accent4'], linestyle='--', linewidth=1, label='limit = 1')
ax.set_xlim(1e-3, 3)
ax.set_title('Analysis: lim sin(x)/x = 1  (verified)', color=THEME['fg'], fontweight='bold', fontsize=11)
ax.legend(fontsize=8, facecolor='#313244', edgecolor=THEME['grid'], labelcolor=THEME['text'])
ax.grid(True, alpha=0.15, color=THEME['text'])
ax.tick_params(colors=THEME['text'], labelsize=8)
for spine in ax.spines.values(): spine.set_color(THEME['grid'])
# Add series convergence inset
x_s = np.arange(1, 21)
partial = np.cumsum(1/x_s**2)
ax_inset = ax.inset_axes([0.55, 0.55, 0.4, 0.35])
ax_inset.set_facecolor('#313244')
ax_inset.plot(x_s, partial, 'o-', color=THEME['accent2'], markersize=3, linewidth=1)
ax_inset.axhline(y=np.pi**2/6, color=THEME['accent4'], linestyle='--', linewidth=0.8, label='pi^2/6')
ax_inset.set_title('Sum 1/n^2 = pi^2/6', fontsize=7, color=THEME['text'])
ax_inset.tick_params(colors=THEME['text'], labelsize=6)
ax_inset.legend(fontsize=6, facecolor='#313244', edgecolor=THEME['grid'], labelcolor=THEME['text'])

# --- Verification Pipeline ---
ax = axes[1, 1]
ax.set_facecolor(THEME['bg'])
ax.set_xlim(0, 10)
ax.set_ylim(0, 6)
ax.axis('off')
levels = [
    (1, 'SymPy Symbolic', THEME['accent1'], 'Identity checks, FOC/SOC, Hessian'),
    (2, 'Monte Carlo 10K', THEME['accent2'], 'Random param testing, turning points'),
    (3, 'SageMath CAS', THEME['accent4'], 'Independent engine cross-check'),
    (4, 'Lean 4 Proof', THEME['accent5'], 'Formal proof template generation'),
    (5, 'QED Multi-Agent', THEME['accent3'], 'Proposer + Critic + Judge'),
]
ax.text(5, 5.5, '5-Level Verification Pipeline', ha='center', fontsize=11,
        color=THEME['fg'], fontweight='bold')
for i, (level, name, color, desc) in enumerate(levels):
    y = 4.3 - i * 0.9
    box = FancyBboxPatch((0.5, y-0.35), 9, 0.7, boxstyle='round,pad=0.1',
                          facecolor=color, edgecolor='none', alpha=0.25)
    ax.add_patch(box)
    ax.text(1.0, y, f'L{level}', fontsize=12, color=color, fontweight='bold', va='center')
    ax.text(2.0, y, name, fontsize=10, color=THEME['fg'], fontweight='bold', va='center')
    ax.text(2.0, y-0.28, desc, fontsize=8, color=THEME['text'], va='center')
    check = ax.text(9.0, y, 'PASS', fontsize=9, color=THEME['accent2'], fontweight='bold', va='center',
                    ha='center', bbox=dict(boxstyle='round,pad=0.2', facecolor='#313244', edgecolor=THEME['grid']))

fig.tight_layout(pad=2)
overview_path = os.path.join(DEMO_DIR, 'demo_overview.png')
fig.savefig(overview_path, dpi=150, bbox_inches='tight', facecolor=THEME['bg'])
plt.close(fig)
print(f'Overview saved: {overview_path}')

# ============================================================
# Figure 2: Architecture Diagram (flow chart style)
# ============================================================
fig2, ax2 = plt.subplots(figsize=(14, 8))
fig2.patch.set_facecolor(THEME['bg'])
ax2.set_facecolor(THEME['bg'])
ax2.set_xlim(0, 14)
ax2.set_ylim(0, 8)
ax2.axis('off')

# User
ax2.text(7, 7.3, 'User Input: "solve y\'\' + 3y\' + 2y = 0"', ha='center', fontsize=12,
         color=THEME['fg'], fontweight='bold',
         bbox=dict(boxstyle='round,pad=0.3', facecolor='#313244', edgecolor=THEME['accent1']))

# LLM Layer
boxes = [
    (7, 6.0, 12, 0.8, THEME['accent5'], 'LLM Agent (Claude / GPT)', 'Plans derivation, selects tools, explains results. Requires API Key.'),
    (7, 5.0, 12, 0.8, THEME['accent1'], 'Harness Layer', 'SkillRegistry + ToolRouter + Orchestrator. Makes tool-calling predictable.'),
]
for x, y, w, h, color, title, desc in boxes:
    box = FancyBboxPatch((x-w/2, y-h/2), w, h, boxstyle='round,pad=0.15',
                          facecolor=color, edgecolor='none', alpha=0.2)
    ax2.add_patch(box)
    ax2.text(x, y+0.2, title, ha='center', fontsize=11, color=color, fontweight='bold')
    ax2.text(x, y-0.2, desc, ha='center', fontsize=9, color=THEME['text'])

# Engine boxes
engine_names = ['Symbolic', 'Numerical', 'Analysis', 'PDE', 'Verification', 'SageMath', 'MultiAgent', 'Document']
engine_colors = [THEME['accent1'], THEME['accent2'], THEME['accent3'], THEME['accent4'],
                 THEME['accent5'], THEME['accent1'], THEME['accent3'], THEME['accent2']]
for i, (name, color) in enumerate(zip(engine_names, engine_colors)):
    x = 1.2 + i * 1.6
    box = FancyBboxPatch((x-0.6, 3.3), 1.2, 0.6, boxstyle='round,pad=0.08',
                          facecolor=color, edgecolor='none', alpha=0.3)
    ax2.add_patch(box)
    ax2.text(x, 3.6, name, ha='center', fontsize=8, color=color, fontweight='bold')

ax2.text(7, 3.0, '12 Engines — Zero API Keys, All Local Computation', ha='center',
         fontsize=9, color=THEME['text'])

# Output
box = FancyBboxPatch((1, 1.5), 12, 1.2, boxstyle='round,pad=0.15',
                      facecolor=THEME['accent2'], edgecolor='none', alpha=0.15)
ax2.add_patch(box)
ax2.text(7, 2.3, 'Output', ha='center', fontsize=11, color=THEME['accent2'], fontweight='bold')
ax2.text(7, 1.9, 'Markdown Report  +  LaTeX Appendix  +  DOCX  +  JSON Data  +  Lean 4 Proof  +  Visualizations',
         ha='center', fontsize=9, color=THEME['text'])

# Arrows
for y in [(6.4, 6.9), (5.4, 6.4), (3.9, 5.4), (2.7, 3.9)]:
    ax2.annotate('', xy=(7, y[1]), xytext=(7, y[0]),
                arrowprops=dict(arrowstyle='->', color=THEME['grid'], lw=1.5))

arch_path = os.path.join(DEMO_DIR, 'demo_architecture.png')
fig2.savefig(arch_path, dpi=150, bbox_inches='tight', facecolor=THEME['bg'])
plt.close(fig2)
print(f'Architecture saved: {arch_path}')

# ============================================================
# Figure 3: PDE Gallery (Heat + Wave + Laplace)
# ============================================================
fig3, axes3 = plt.subplots(1, 3, figsize=(16, 5))
fig3.patch.set_facecolor(THEME['bg'])

# Heat
ax = axes3[0]; ax.set_facecolor(THEME['bg'])
nx, nt = 50, 100
u = np.zeros((nt, nx)); u[0, nx//4:3*nx//4] = 1.0
r = 0.4
for n in range(nt-1):
    u[n+1, 1:-1] = u[n, 1:-1] + r*(u[n, 2:] - 2*u[n, 1:-1] + u[n, :-2])
im0 = ax.imshow(u[::5, :], aspect='auto', cmap='plasma', interpolation='bilinear')
ax.set_title('Heat: u_t = alpha u_xx', color=THEME['fg'], fontweight='bold', fontsize=11)
ax.tick_params(colors=THEME['text'], labelsize=8)

# Wave
ax = axes3[1]; ax.set_facecolor(THEME['bg'])
u2 = np.zeros((nt, nx)); cfl = 0.8; r2 = cfl**2
x_w = np.linspace(0, 1, nx); u2[0, :] = np.sin(2*np.pi*x_w)*np.exp(-50*(x_w-0.5)**2)
u2[1, 1:-1] = u2[0, 1:-1] + 0.5*r2*(u2[0, 2:] - 2*u2[0, 1:-1] + u2[0, :-2])
for n in range(1, nt-1):
    u2[n+1, 1:-1] = 2*u2[n, 1:-1] - u2[n-1, 1:-1] + r2*(u2[n, 2:] - 2*u2[n, 1:-1] + u2[n, :-2])
im1 = ax.imshow(u2[::4, :], aspect='auto', cmap='plasma', interpolation='bilinear')
ax.set_title('Wave: u_tt = c^2 u_xx', color=THEME['fg'], fontweight='bold', fontsize=11)
ax.tick_params(colors=THEME['text'], labelsize=8)

# Laplace
ax = axes3[2]; ax.set_facecolor(THEME['bg'])
nx2, ny2 = 40, 40
u3 = np.zeros((ny2, nx2)); u3[0, :] = np.linspace(0, 1, nx2)
for _ in range(2000):
    u3[1:-1, 1:-1] = 0.25*(u3[2:, 1:-1] + u3[:-2, 1:-1] + u3[1:-1, 2:] + u3[1:-1, :-2])
im2 = ax.imshow(u3, aspect='auto', cmap='plasma', interpolation='bilinear', origin='lower')
ax.set_title('Laplace: u_xx + u_yy = 0', color=THEME['fg'], fontweight='bold', fontsize=11)
ax.tick_params(colors=THEME['text'], labelsize=8)

fig3.tight_layout()
pde_gallery_path = os.path.join(DEMO_DIR, 'demo_pde_gallery.png')
fig3.savefig(pde_gallery_path, dpi=150, bbox_inches='tight', facecolor=THEME['bg'])
plt.close(fig3)
print(f'PDE gallery saved: {pde_gallery_path}')

# ============================================================
# Figure 4: Verification Flow (horizontal pipeline)
# ============================================================
fig4, ax4 = plt.subplots(figsize=(16, 3))
fig4.patch.set_facecolor(THEME['bg']); ax4.set_facecolor(THEME['bg'])
ax4.set_xlim(0, 16); ax4.set_ylim(0, 1.5); ax4.axis('off')

steps = [
    ('Claim', THEME['fg']),
    ('SymPy\nSymbolic', THEME['accent1']),
    ('Monte Carlo\n10K Samples', THEME['accent2']),
    ('SageMath\nCross-Check', THEME['accent4']),
    ('Lean 4\nProof', THEME['accent5']),
    ('QED\nMulti-Agent', THEME['accent3']),
    ('Verdict:\nACCEPTED', THEME['accent2']),
]
for i, (label, color) in enumerate(steps):
    x = 1.2 + i * 2.1
    box = FancyBboxPatch((x-0.85, 0.5), 1.7, 0.6, boxstyle='round,pad=0.1',
                          facecolor=color, edgecolor='none', alpha=0.3)
    ax4.add_patch(box)
    ax4.text(x, 0.8, label, ha='center', fontsize=9, color=color, fontweight='bold', va='center')
    if i < len(steps) - 1:
        ax4.annotate('', xy=(x+1.1, 0.8), xytext=(x+0.9, 0.8),
                    arrowprops=dict(arrowstyle='->', color=THEME['grid'], lw=1.5))

ax4.text(8, 1.2, '5-Level Verification Pipeline: claim enters, verified result exits',
         ha='center', fontsize=11, color=THEME['fg'], fontweight='bold')
verify_path = os.path.join(DEMO_DIR, 'demo_verification.png')
fig4.savefig(verify_path, dpi=150, bbox_inches='tight', facecolor=THEME['bg'])
plt.close(fig4)
print(f'Verification saved: {verify_path}')

print('\nAll 4 advanced demo images generated.')
