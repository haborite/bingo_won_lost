import csv
import os
import sys
import matplotlib.pyplot as plt

# index -> (row, col)
# idx: 0 1 2
#      3   4
#      5 6 7
IDX_TO_RC = [
    (0, 0),  # 0
    (0, 1),  # 1
    (0, 2),  # 2
    (1, 0),  # 3
    (1, 2),  # 4
    (2, 0),  # 5
    (2, 1),  # 6
    (2, 2),  # 7
]


def parse_pattern_key(pattern_key: str):
    """
    PatternKey は "0->3;1->5" のような形（i->i は省略済み）。
    "[]" の場合は移動なし。
    """
    pattern_key = pattern_key.strip()
    if pattern_key == "[]" or pattern_key == "":
        return []
    moves = []
    for part in pattern_key.split(";"):
        part = part.strip()
        if not part:
            continue
        if "->" not in part:
            continue
        f_str, t_str = part.split("->")
        f = int(f_str.strip())
        t = int(t_str.strip())
        moves.append((f, t))
    return moves


def draw_pattern(moves, delta_pair, pattern_key, moved_count, total_count, out_path):
    fig, ax = plt.subplots(figsize=(4, 4))

    # grid lines
    for x in range(4):
        ax.axvline(x - 0.5, linewidth=1)
    for y in range(4):
        ax.axhline(y - 0.5, linewidth=1)

    # center free cell (1,1) を少し塗る
    ax.add_patch(
        plt.Rectangle(
            (1 - 0.5, 1 - 0.5),
            1.0,
            1.0,
            facecolor="#EEEEEE",
            edgecolor="none",
            zorder=0,
        )
    )

    # cell index labels
    for idx, (r, c) in enumerate(IDX_TO_RC):
        ax.text(
            c,
            r,
            str(idx),
            ha="center",
            va="center",
            fontsize=10,
        )

    # arrows for moves
    for f_idx, t_idx in moves:
        r0, c0 = IDX_TO_RC[f_idx]
        r1, c1 = IDX_TO_RC[t_idx]
        ax.annotate(
            "",
            xy=(c1, r1),
            xytext=(c0, r0),
            arrowprops=dict(arrowstyle="->", linewidth=2),
        )

    ax.set_xlim(-0.5, 2.5)
    ax.set_ylim(2.5, -0.5)  # row 0 を上に
    ax.set_aspect("equal")
    ax.set_xticks([])
    ax.set_yticks([])

    title = f"MovedCount={moved_count}, TotalCount={total_count}\n" \
            f"Pattern: {pattern_key}\n" \
            f"Delta = {delta_pair} (from 50%)"
    ax.set_title(title, fontsize=9)

    plt.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)


def main():
    if len(sys.argv) != 2:
        print("Usage: python draw_patterns_by_movedcount.py N")
        print("  (N = MovedCount)")
        sys.exit(1)

    try:
        target_moved = int(sys.argv[1])
    except ValueError:
        print("N must be an integer.")
        sys.exit(1)

    in_csv = "patterns_reduced_by_D4_and_inversion.csv"
    out_dir = f"patterns_moved{target_moved}"
    os.makedirs(out_dir, exist_ok=True)

    with open(in_csv, newline="", encoding="utf_8_sig") as f:
        reader = csv.DictReader(f)
        idx = 0
        for row in reader:
            moved = int(row["MovedCount"])
            if moved != target_moved:
                continue

            pattern_key = row["PatternKey"].strip()
            total_count = int(row["TotalCount"])
            delta_pair = row["DeltaPair"].strip()  # "±0.00...."

            moves = parse_pattern_key(pattern_key)

            out_path = os.path.join(out_dir, f"pattern_m{target_moved}_{idx:03d}.png")
            draw_pattern(moves, delta_pair, pattern_key, moved, total_count, out_path)
            idx += 1

    print(f"Saved {idx} patterns with MovedCount={target_moved} to {out_dir}/")


if __name__ == "__main__":
    main()
