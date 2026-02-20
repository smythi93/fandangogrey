import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from run_experiment import idx_to_linestyle

legend_elements = [
    Line2D([0], [0], color="#ff7f0e", lw=2, linestyle=idx_to_linestyle[0], label='Execution Feedback'),
    Line2D([0], [0], color="#1f77b4", lw=2, linestyle=idx_to_linestyle[1], label='Input Spec.'),
    Line2D([0], [0], color="#2ca02c", lw=2, linestyle=idx_to_linestyle[2], label='Input Spec. + Execution Feedback')
]

fig = plt.figure(figsize=(2,1))
ax = fig.add_subplot(111)
ax.axis('off')

leg = ax.legend(handles=legend_elements, loc='center', ncol=3)
fig.canvas.draw()

bbox = leg.get_window_extent()
bbox = bbox.transformed(fig.dpi_scale_trans.inverted())
fig.savefig("legend_only.pdf", bbox_inches=bbox.expanded(1.1, 1.3), dpi=300)
