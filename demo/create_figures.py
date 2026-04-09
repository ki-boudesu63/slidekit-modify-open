"""ダミー論文用の図を生成する"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import os

OUT = os.path.join(os.path.dirname(__file__), "figures")
os.makedirs(OUT, exist_ok=True)

plt.rcParams['font.size'] = 12
plt.rcParams['figure.dpi'] = 200

# === Fig 1: Study Design Flowchart ===
fig, ax = plt.subplots(figsize=(8, 4))
ax.set_xlim(0, 10)
ax.set_ylim(0, 5)
ax.axis('off')
ax.set_title("Figure 1. Study Design", fontsize=14, fontweight='bold', pad=15)

boxes = [
    (1, 3.5, "Pre-implementation\nApr–Sep 2025\n(n = 9,105)", "#4A90D9"),
    (4, 3.5, "AI System\nDeployed\nOct 1, 2025", "#E67E22"),
    (7, 3.5, "Post-implementation\nOct 2025–Mar 2026\n(n = 9,315)", "#27AE60"),
]
for x, y, text, color in boxes:
    rect = mpatches.FancyBboxPatch((x - 1.2, y - 0.8), 2.4, 1.6,
                                    boxstyle="round,pad=0.15",
                                    facecolor=color, edgecolor='#333', alpha=0.85)
    ax.add_patch(rect)
    ax.text(x, y, text, ha='center', va='center', fontsize=9, color='white', fontweight='bold')

ax.annotate('', xy=(2.8, 3.5), xytext=(2.2, 3.5),
            arrowprops=dict(arrowstyle='->', color='#555', lw=2))
ax.annotate('', xy=(5.8, 3.5), xytext=(5.2, 3.5),
            arrowprops=dict(arrowstyle='->', color='#555', lw=2))

# 下部: outcomes
outcomes = "Primary: Door-to-doctor time  |  Secondary: Triage accuracy, Satisfaction, 72h return rate"
ax.text(5, 1.5, outcomes, ha='center', va='center', fontsize=9, color='#555',
        bbox=dict(boxstyle='round,pad=0.5', facecolor='#F0F4F8', edgecolor='#CCC'))

fig.tight_layout()
fig.savefig(os.path.join(OUT, "fig1_study_design.png"), bbox_inches='tight', facecolor='white')
plt.close()

# === Fig 2: Door-to-Doctor Time (Bar + Box-like) ===
fig, ax = plt.subplots(figsize=(6, 4.5))

categories = ['Overall', 'Level 1\n(Resuscitation)', 'Walk-in', 'Ambulance']
pre = [42, 8.0, 48, 22]
post = [31, 5.2, 33, 18]

x = np.arange(len(categories))
w = 0.35
bars1 = ax.bar(x - w/2, pre, w, label='Pre-AI', color='#BDC3C7', edgecolor='#888')
bars2 = ax.bar(x + w/2, post, w, label='Post-AI', color='#2980B9', edgecolor='#1A5276')

ax.set_ylabel('Median Time (minutes)', fontweight='bold')
ax.set_title('Figure 2. Door-to-Doctor Time', fontsize=13, fontweight='bold')
ax.set_xticks(x)
ax.set_xticklabels(categories, fontsize=9)
ax.legend(framealpha=0.9)
ax.set_ylim(0, 60)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)

for bar_group in [bars1, bars2]:
    for bar in bar_group:
        h = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2, h + 1, f'{h:.0f}' if h >= 10 else f'{h:.1f}',
                ha='center', va='bottom', fontsize=8, fontweight='bold')

# p値
ax.text(0, 55, 'p < 0.001', ha='center', fontsize=8, color='red', fontstyle='italic')

fig.tight_layout()
fig.savefig(os.path.join(OUT, "fig2_door_to_doctor.png"), bbox_inches='tight', facecolor='white')
plt.close()

# === Fig 3: Triage Accuracy by Level ===
fig, ax = plt.subplots(figsize=(6, 4.5))

levels = ['Level 1', 'Level 2', 'Level 3', 'Level 4', 'Level 5', 'Overall']
pre_acc = [85, 71, 79, 82, 76, 78.3]
post_acc = [93, 88, 91, 90, 84, 89.1]

x = np.arange(len(levels))
w = 0.35
ax.bar(x - w/2, pre_acc, w, label='Pre-AI', color='#F5B7B1', edgecolor='#C0392B')
ax.bar(x + w/2, post_acc, w, label='Post-AI', color='#82E0AA', edgecolor='#1E8449')

ax.set_ylabel('Accuracy (%)', fontweight='bold')
ax.set_title('Figure 3. Triage Accuracy by Level', fontsize=13, fontweight='bold')
ax.set_xticks(x)
ax.set_xticklabels(levels, fontsize=9)
ax.legend(framealpha=0.9)
ax.set_ylim(60, 100)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)

fig.tight_layout()
fig.savefig(os.path.join(OUT, "fig3_triage_accuracy.png"), bbox_inches='tight', facecolor='white')
plt.close()

# === Fig 4: Patient Satisfaction ===
fig, ax = plt.subplots(figsize=(5, 3.5))

cats = ['Pre-AI', 'Post-AI']
scores = [3.4, 4.1]
colors = ['#BDC3C7', '#2980B9']
bars = ax.bar(cats, scores, color=colors, edgecolor='#555', width=0.5)

ax.set_ylabel('Mean Score (1–5)', fontweight='bold')
ax.set_title('Figure 4. Patient Satisfaction', fontsize=13, fontweight='bold')
ax.set_ylim(0, 5)
ax.axhline(y=3, color='#CCC', linestyle='--', linewidth=0.8, label='Neutral (3.0)')
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)

for bar, score in zip(bars, scores):
    ax.text(bar.get_x() + bar.get_width()/2, score + 0.1, f'{score:.1f}',
            ha='center', va='bottom', fontsize=14, fontweight='bold')

ax.text(0.5, 0.95, 'p < 0.001', ha='center', fontsize=9, color='red',
        fontstyle='italic', transform=ax.transAxes)

fig.tight_layout()
fig.savefig(os.path.join(OUT, "fig4_satisfaction.png"), bbox_inches='tight', facecolor='white')
plt.close()

print("Generated 4 figures in", OUT)
for f in sorted(os.listdir(OUT)):
    print(f"  {f}")
