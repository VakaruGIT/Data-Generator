# routing_generator.py

import pandas as pd
import numpy as np
from pathlib import Path

SEED = 42
np.random.seed(SEED)
rng = np.random.default_rng(SEED)

OP_SEQS = [10, 20, 30, 40, 50]
WC_LIST = [f"WC{str(i).zfill(2)}" for i in range(1, 21)]
MACH_CLASSES = ["CNC", "PRESS", "MILL", "ROBOT", "GRIND"]


def generate_routings(material_master_path="out/material_master.csv"):
    mm = pd.read_csv(material_master_path)
    routings = []
    for _, row in mm.iterrows():
        n_ops = rng.integers(1, 4)
        ops = rng.choice(OP_SEQS, size=n_ops, replace=False)
        ops.sort()
        for op in ops:
            routings.append({
                "MaterialNumber": row["MaterialNumber"],
                "OperationSeq": op,
                "WorkCenter": rng.choice(WC_LIST),
                "MachineClass": rng.choice(MACH_CLASSES),
                "SetupTime_min": int(np.clip(rng.normal(30, 10), 5, 120)),
                "RunTime_min": int(np.clip(rng.normal(300, 60), 30, 600))
            })
    return pd.DataFrame(routings)

if __name__ == "__main__":
    Path("out").mkdir(exist_ok=True)
    df = generate_routings()
    df.to_csv("out/routing_table.csv", index=False)
    print(f"✅ routing_table.csv written | rows={len(df):,}")
