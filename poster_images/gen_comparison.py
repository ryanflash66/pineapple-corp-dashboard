import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

fig = plt.figure(figsize=(18, 11))

# Title at top
fig.text(0.5, 0.97, 'Base Model vs. Fine-Tuned IRP-AI: Same Prompt Comparison',
         ha='center', fontsize=18, fontweight='bold', color='#222')
fig.text(0.5, 0.94, 'Prompt: "Create a detailed incident response playbook" \u2014 Ransomware on Windows AD Server',
         ha='center', fontsize=12, color='#555', fontstyle='italic')

# ==================== LEFT PANEL (Base) ====================
ax1 = fig.add_axes([0.02, 0.08, 0.47, 0.83])
ax1.set_xlim(0, 10)
ax1.set_ylim(0, 10)
ax1.set_facecolor('#FFF8F8')
ax1.set_xticks([])
ax1.set_yticks([])
for spine in ax1.spines.values():
    spine.set_edgecolor('#D32F2F')
    spine.set_linewidth(3)

# Header
ax1.add_patch(plt.Rectangle((0, 9.2), 10, 0.8, facecolor='#D32F2F', clip_on=False))
ax1.text(5, 9.6, 'Base Llama 3.1 8B (No Fine-Tuning)', ha='center', va='center',
         fontsize=16, fontweight='bold', color='white')

base_lines = [
    ('1. Upon detection of the ransomware, the', '#444'),
    ('   following actions should be taken:', '#444'),
    ('   1. Identify the source of the infection', '#444'),
    ('   2. Quarantine the affected systems', '#444'),
    ('   3. Perform a full system backup', '#444'),
    ('   4. Restore the system from the backup', '#444'),
    ('   5. Update the anti-virus software', '#444'),
    ('   6. Check for any suspicious files', '#444'),
    ('   7. Perform a full system audit', '#444'),
    ('   8. Implement additional security measures', '#444'),
    ('', '#444'),
    ('2. The incident response team should also', '#999'),
    ('   investigate the source of the infection...', '#999'),
    ('3. The incident response team should also', '#999'),
    ('   coordinate with law enforcement...', '#999'),
    ('4. The incident response team should also', '#999'),
    ('   work with the affected organization...', '#999'),
    ('5. The incident response team should also', '#999'),
    ('   work with the affected organization...', '#999'),
    ('6. The incident response team should also', '#999'),
    ('   work with the affected organization...', '#999'),
    ('7. The incident response team should also...', '#999'),
    ('', '#999'),
    ('     [repeats until truncated at 512 tokens]', '#D32F2F'),
]

y = 8.9
for text, color in base_lines:
    ax1.text(0.4, y, text, fontsize=11, fontfamily='monospace', color=color, va='top')
    y -= 0.345

# Bottom badges
badge_y = 0.45
badges_left = [
    ('NIST Phases: 0/5', '#D32F2F'),
    ('Asset Refs: 0/5', '#D32F2F'),
    ('Truncated', '#D32F2F'),
    ('Repetitive', '#D32F2F'),
]
x = 0.3
for label, color in badges_left:
    w = len(label) * 0.165 + 0.4
    ax1.add_patch(FancyBboxPatch((x, badge_y - 0.15), w, 0.55,
                  boxstyle="round,pad=0.1", facecolor=color, alpha=0.12,
                  edgecolor=color, linewidth=1.5))
    ax1.text(x + w/2, badge_y + 0.12, label, ha='center', va='center',
             fontsize=10.5, fontweight='bold', color=color)
    x += w + 0.25

# ==================== RIGHT PANEL (Fine-Tuned) ====================
ax2 = fig.add_axes([0.51, 0.08, 0.47, 0.83])
ax2.set_xlim(0, 10)
ax2.set_ylim(0, 10)
ax2.set_facecolor('#F5FFF5')
ax2.set_xticks([])
ax2.set_yticks([])
for spine in ax2.spines.values():
    spine.set_edgecolor('#2E7D32')
    spine.set_linewidth(3)

# Header
ax2.add_patch(plt.Rectangle((0, 9.2), 10, 0.8, facecolor='#2E7D32', clip_on=False))
ax2.text(5, 9.6, 'Fine-Tuned IRP-AI (LoRA)', ha='center', va='center',
         fontsize=16, fontweight='bold', color='white')

ft_sections = [
    ('Phase: Identification', '#1B5E20', True),
    ('Action: Analyze EDR alert, confirm', '#333', False),
    ('        ransomware on srv-dc-01', '#333', False),
    ('Tools:  edr-console', '#333', False),
    ('Response time: 15 min', '#333', False),
    ('', '#333', False),
    ('Phase: Containment', '#1B5E20', True),
    ('Action: Isolate srv-dc-01, block', '#333', False),
    ('        ransomware traffic', '#333', False),
    ('Tools:  fw-perimeter-01, edr-console', '#333', False),
    ('Response time: 10 min', '#333', False),
    ('', '#333', False),
    ('Phase: Eradication', '#1B5E20', True),
    ('Action: Remove ransomware from', '#333', False),
    ('        srv-dc-01, restore from backup', '#333', False),
    ('Tools:  edr-console, backup-veeam-01', '#333', False),
    ('Response time: 60 min', '#333', False),
    ('', '#333', False),
    ('Phase: Recovery', '#1B5E20', True),
    ('Action: Restore srv-dc-01, monitor', '#333', False),
    ('Tools:  edr-console, siem-splunk-01', '#333', False),
    ('Response time: 120 min', '#333', False),
    ('', '#333', False),
    ('Phase: Lessons Learned', '#1B5E20', True),
    ('Action: Update IR plan, train staff', '#333', False),
    ('Tools:  MISP, Tenable', '#333', False),
    ('Response time: 180 min', '#333', False),
    ('', '#333', False),
    ('Status: Resolved | Total: 385 min', '#1B5E20', True),
]

y = 8.9
for text, color, bold in ft_sections:
    weight = 'bold' if bold else 'normal'
    size = 11.5 if bold else 11
    ax2.text(0.4, y, text, fontsize=size, fontfamily='monospace', color=color,
             va='top', fontweight=weight)
    y -= 0.3

# Bottom badges
x = 0.3
badges_right = [
    ('NIST Phases: 5/5', '#2E7D32'),
    ('Asset Refs: 5/5', '#2E7D32'),
    ('Structured', '#2E7D32'),
    ('Complete', '#2E7D32'),
]
for label, color in badges_right:
    w = len(label) * 0.165 + 0.4
    ax2.add_patch(FancyBboxPatch((x, badge_y - 0.15), w, 0.55,
                  boxstyle="round,pad=0.1", facecolor=color, alpha=0.12,
                  edgecolor=color, linewidth=1.5))
    ax2.text(x + w/2, badge_y + 0.12, label, ha='center', va='center',
             fontsize=10.5, fontweight='bold', color=color)
    x += w + 0.25

# Center "vs" circle
fig.text(0.5, 0.5, 'vs', ha='center', va='center', fontsize=22, fontweight='bold',
         color='#888',
         bbox=dict(boxstyle='circle,pad=0.3', facecolor='white', edgecolor='#CCC', linewidth=2))

plt.savefig('poster_images/base_vs_finetuned_comparison.png', dpi=250, bbox_inches='tight', facecolor='white')
print('Saved base_vs_finetuned_comparison.png')
plt.close()
