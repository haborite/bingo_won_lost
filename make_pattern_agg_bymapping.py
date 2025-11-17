import csv

# ===== 対称操作周り（さっきのコード） =====

IDX_TO_RC = [
    (0, 0),
    (0, 1),
    (0, 2),
    (1, 0),
    (1, 2),
    (2, 0),
    (2, 1),
    (2, 2),
]

def rc_from_idx(i: int):
    return IDX_TO_RC[i]

def idx_from_rc(r: int, c: int) -> int:
    for idx, (rr, cc) in enumerate(IDX_TO_RC):
        if rr == r and cc == c:
            return idx
    raise ValueError(f"invalid (r,c)=({r},{c})")

def rot90(r: int, c: int):
    return (c, 2 - r)

def rot180(r: int, c: int):
    return (2 - r, 2 - c)

def rot270(r: int, c: int):
    return (2 - c, r)

def ref_v(r: int, c: int):
    return (r, 2 - c)

def ref_h(r: int, c: int):
    return (2 - r, c)

def ref_d1(r: int, c: int):
    return (c, r)

def ref_d2(r: int, c: int):
    return (2 - c, 2 - r)

SYM_OPS = [
    ("Id",    lambda r, c: (r, c)),
    ("R90",   rot90),
    ("R180",  rot180),
    ("R270",  rot270),
    ("RefV",  ref_v),
    ("RefH",  ref_h),
    ("RefD1", ref_d1),
    ("RefD2", ref_d2),
]

def apply_sym_to_idx(op, i: int) -> int:
    r, c = rc_from_idx(i)
    r2, c2 = op(r, c)
    return idx_from_rc(r2, c2)

def canonical_key_D4_from_perm(perm):
    best = None
    for name, op in SYM_OPS:
        pairs = []
        for i in range(8):
            j = perm[i]
            i2 = apply_sym_to_idx(op, i)
            j2 = apply_sym_to_idx(op, j)
            pairs.append((i2, j2))
        pairs.sort(key=lambda p: p[0])
        s = ";".join(f"{i}->{j}" for i, j in pairs)
        if best is None or s < best:
            best = s
    return best

# ===== PatternKey（簡略）から perm を復元 =====

def perm_from_simplified_pattern_key(pattern_key: str):
    perm = list(range(8))
    pattern_key = pattern_key.strip()
    if pattern_key == "[]" or pattern_key == "":
        return perm
    for part in pattern_key.split(";"):
        part = part.strip()
        if not part:
            continue
        if "->" not in part:
            continue
        f_str, t_str = part.split("->")
        f = int(f_str.strip())
        t = int(t_str.strip())
        perm[f] = t
    return perm

def perm_from_full_key(full_key: str):
    perm = list(range(8))
    if full_key.strip() == "[]":
        return perm
    for part in full_key.split(";"):
        part = part.strip()
        if not part:
            continue
        if "->" not in part:
            continue
        f_str, t_str = part.split("->")
        f = int(f_str.strip())
        t = int(t_str.strip())
        perm[f] = t
    return perm

def simplify_full_key(full_key: str) -> str:
    full_key = full_key.strip()
    if not full_key:
        return "[]"
    kept = []
    for part in full_key.split(";"):
        part = part.strip()
        if not part:
            continue
        if "->" not in part:
            continue
        f_str, t_str = part.split("->")
        f = f_str.strip()
        t = t_str.strip()
        if f == t:
            continue
        kept.append(f"{f}->{t}")
    if not kept:
        return "[]"
    return ";".join(kept)

# ===== main =====

def main():
    in_csv = "pattern_agg_by_mapping.csv"
    # D4で束ねた full_key_D4 -> (MovedCount, Count, Delta)
    class_map = {}

    print(f"Reading {in_csv} ...")
    with open(in_csv, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            pattern_key_simpl = row["PatternKey"].strip()
            moved = int(row["MovedCount"])
            count = int(row["Count"])
            delta = float(row["Delta"])

            perm = perm_from_simplified_pattern_key(pattern_key_simpl)
            full_key_D4 = canonical_key_D4_from_perm(perm)

            if full_key_D4 in class_map:
                old_moved, old_count, old_delta = class_map[full_key_D4]
                if old_moved != moved:
                    print("Warning: moved_count mismatch in same D4-class, using first one.")
                # Delta は D4 等価なら同じはずなので、old_delta をそのまま維持
                class_map[full_key_D4] = (old_moved, old_count + count, old_delta)
            else:
                class_map[full_key_D4] = (moved, count, delta)

    print(f"D4-classes: {len(class_map)}")

    # full_key_D4 の集合
    keys = sorted(class_map.keys())
    visited = set()
    reduced_classes = []

    for full_key in keys:
        if full_key in visited:
            continue

        moved, cnt, delta = class_map[full_key]

        perm = perm_from_full_key(full_key)
        # 逆写像
        perm_inv = [0]*8
        for i, j in enumerate(perm):
            perm_inv[j] = i
        inv_key = canonical_key_D4_from_perm(perm_inv)

        if inv_key not in class_map:
            total_count = cnt
            delta_abs = abs(delta)
            rep_full_key = full_key
            rep_simpl = simplify_full_key(full_key)
        else:
            moved2, cnt2, delta2 = class_map[inv_key]
            visited.add(inv_key)
            total_count = cnt + cnt2
            delta_abs = (abs(delta) + abs(delta2)) / 2.0
            rep_simpl_1 = simplify_full_key(full_key)
            rep_simpl_2 = simplify_full_key(inv_key)
            if rep_simpl_2 < rep_simpl_1:
                rep_full_key = inv_key
                rep_simpl = rep_simpl_2
            else:
                rep_full_key = full_key
                rep_simpl = rep_simpl_1

        visited.add(full_key)
        reduced_classes.append((rep_simpl, moved, total_count, delta_abs))

    # ソート：MovedCount → |Delta|大きい順 → PatternKey
    reduced_classes.sort(key=lambda x: (x[1], -x[3], x[0]))

    out_csv = "patterns_reduced_by_D4_and_inversion.csv"
    print(f"Writing {out_csv} ...")
    with open(out_csv, "w", newline="", encoding="utf_8") as f:
        writer = csv.writer(f)
        writer.writerow(["PatternKey", "MovedCount", "TotalCount", "DeltaAbs", "DeltaPair"])
        for pattern_key, moved, total_count, delta_abs in reduced_classes:
            delta_pair = f"±{delta_abs:.10f}"
            writer.writerow([pattern_key, moved, total_count, f"{delta_abs:.10f}", delta_pair])

    print("Done.")

if __name__ == "__main__":
    main()
