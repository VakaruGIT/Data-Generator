# bom_resolver.py

import pandas as pd

def load_bom(path="out/bom_table.csv"):
    return pd.read_csv(path)

def resolve_to_raw(bom_df, material_number):
    """
    Resolve all RAWs under a given FG or SFG using recursive traversal.
    Returns a flat list of raw components with cumulative quantities.
    """
    from collections import defaultdict, deque
    
    resolved = defaultdict(int)
    queue = deque([(material_number, 1)])

    while queue:
        parent, parent_qty = queue.popleft()
        children = bom_df[bom_df["ParentMaterial"] == parent]

        for _, row in children.iterrows():
            child = row["ComponentMaterial"]
            qty = int(row["Quantity"])
            total_qty = qty * parent_qty

            if child.startswith("RAW"):
                resolved[child] += total_qty
            else:
                queue.append((child, total_qty))

    return pd.DataFrame([{"RawMaterial": k, "TotalQty": v} for k, v in resolved.items()])

if __name__ == "__main__":
    bom_df = load_bom()
    material_number = input("Enter FG or SFG material number (e.g. FG0001): ").strip()
    result = resolve_to_raw(bom_df, material_number)
    print(result)
