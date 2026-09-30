"""Render measured data-reduction time and held-out quality without equivalence claims."""
import argparse
import json
import os
from pathlib import Path

os.environ.setdefault('MPLCONFIGDIR', str(Path('.tmp/matplotlib_exp214').resolve()))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--comparison', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    data = json.loads(args.comparison.read_text())
    assert data['status'] == 'PASS_PAIRED_DATA_REDUCTION_COMPARISON'
    arms = ['full12', 'reduced12', 'reduced60']
    labels = ['Полные данные\n12 эпох', 'Сокращённые\n12 эпох', 'Сокращённые\n60 эпох']
    colors = ['#87919b', '#d18331', '#237d70']
    scores = [data['scores'][arm + '_same_single_detector_public_graph'] for arm in arms]
    minutes = [data['training_times'][arm]['all_epochs_including_validation_seconds'] / 60 for arm in arms]
    fig, axes = plt.subplots(1, 2, figsize=(10.7, 5.4))
    for ax, values, ylabel in zip(axes, (scores, minutes), ('Официальный tracking score', 'Обучение + validation, минуты')):
        bars = ax.bar(labels, values, color=colors, width=.62)
        ax.bar_label(bars, labels=[f'{value:.4f}' if ax is axes[0] else f'{value:.1f}' for value in values], padding=4)
        ax.set_ylabel(ylabel)
        ax.set_ylim(0, 1.02 if ax is axes[0] else max(minutes) * 1.2)
        ax.spines[['top', 'right']].set_visible(False)
        ax.grid(axis='y', alpha=.15)
        ax.set_axisbelow(True)
    fig.suptitle('EXP214: сокращение данных — качество при равном времени', fontsize=15, x=.055, ha='left')
    fig.text(.055, .045, '20 целых роликов одного исключённого эмбриона; одинаковый граф и один seed.\nВремя включает все эпохи, в том числе 12 до resume; аугментации не воспроизводятся побитово.', fontsize=9, color='#525b64')
    fig.tight_layout(rect=[0, .13, 1, .94])
    args.output.parent.mkdir(parents=True, exist_ok=True)
    for extension in ('png', 'svg'):
        fig.savefig(args.output.with_suffix('.' + extension), dpi=160, bbox_inches='tight')
    plt.close(fig)


if __name__ == '__main__':
    main()
