# nal.py (Retrofitted Final Time Series Generator with OperatorID)

import pandas as pd
import numpy as np
import random
from datetime import timedelta
from pathlib import Path

# Config
SEED = 13
NUM_RECORDS = 50000
np.random.seed(SEED)
rng = np.random.default_rng(SEED)
random.seed(SEED)

# Operator pool
OP_IDS = [f"OP{str(i).zfill(3)}" for i in range(1, 61)]

# Load master data
mm = pd.read_csv("out/material_master.csv")
routings = pd.read_csv("out/routing_table.csv")
orders = pd.read_csv("out/production_orders.csv")

# Only use FGs for production
fg_materials = mm[mm.MaterialType == "FG"]
routings_fg = routings[routings.MaterialNumber.isin(fg_materials.MaterialNumber)]

# Generate records with realistic timing
records = []
order_timestamps = {}  # Track last timestamp for each order to ensure realistic sequencing

for i in range(NUM_RECORDS):
    order = orders.sample(1).iloc[0]
    mat = mm[mm.MaterialNumber == order.MaterialNumber].iloc[0]
    routing_subset = routings_fg[routings_fg.MaterialNumber == mat.MaterialNumber]
    if routing_subset.empty:
        continue
    op = routing_subset.sample(1).iloc[0]  # pick one routing step
    
    # Create more realistic timestamps with random minutes and seconds
    base_timestamp = pd.to_datetime(order.OrderDate) + timedelta(hours=int(rng.integers(0, 720)))
    # Add random minutes (0-59) and seconds (0-59)
    random_minutes = int(rng.integers(0, 60))
    random_seconds = int(rng.integers(0, 60))
    timestamp = base_timestamp + timedelta(minutes=random_minutes, seconds=random_seconds)
    
    # Add realistic work shift patterns (slightly favor day shifts)
    hour = timestamp.hour
    weekday = timestamp.weekday()  # 0=Monday, 6=Sunday
    
    # Weekend operations reduced (but not eliminated for 24/7 operations)
    if weekday >= 5:  # Saturday or Sunday
        if rng.random() < 0.4:  # 40% chance to skip weekend operations
            continue
    
    # Night shift operations reduced
    if hour < 6 or hour > 22:  # Night shift - reduce probability
        if rng.random() < 0.3:  # 30% chance to skip night operations
            continue
    elif 6 <= hour <= 14:  # Day shift - normal operations
        pass
    elif 14 <= hour <= 22:  # Evening shift - normal operations
        pass
    
    # Ensure sequential operations for the same order have realistic time gaps
    order_id = order.ProductionOrderID
    if order_id in order_timestamps:
        # Add realistic gap based on actual operation duration
        last_timestamp = order_timestamps[order_id]
        # Gap = previous operation duration + changeover + transport + buffer
        realistic_gap = timedelta(
            minutes=int(setup_act + run_act + changeover_time + transport_time + int(rng.integers(0, 30)))
        )
        if timestamp <= last_timestamp + realistic_gap:
            timestamp = last_timestamp + realistic_gap
    
    order_timestamps[order_id] = timestamp

    # Plan vs actual with more realistic timing
    setup_plan = np.clip(rng.normal(30, 10), 5, 120)
    run_plan   = np.clip(rng.normal(300, 60), 30, 600)
    setup_act  = setup_plan * rng.uniform(0.7, 1.5)
    run_act    = run_plan   * rng.uniform(0.6, 1.7)
    
    # Add realistic changeover and transport time
    changeover_time = int(rng.integers(10, 45))  # 10-45 minutes for changeover
    transport_time = int(rng.integers(5, 20))    # 5-20 minutes for material transport

    # Lot sizes and yield
    lot_plan = rng.integers(50, 500)
    lot_act  = max(1, round(lot_plan + rng.normal(0, 20)))
    scrap    = rng.binomial(10, 0.1)

    records.append({
        "RecordDateTime": timestamp,
        "ProductionOrderID": order.ProductionOrderID,
        "PlantID": order.PlantID,
        "WorkCenterID": op.WorkCenter,
        "MachineClass": op.MachineClass,
        "OperatorID": rng.choice(OP_IDS),

        "MaterialNumber": mat.MaterialNumber,
        "MaterialName": mat.MaterialName,
        "ProductComplexity": mat.ProductComplexity,

        "OperationSeq": op.OperationSeq,
        "SetupTime_Planned_min": round(setup_plan),
        "RunTime_Planned_min": round(run_plan),
        "SetupTime_Actual_min": round(setup_act),
        "RunTime_Actual_min": round(run_act),

        "LotSize_Planned": lot_plan,
        "LotSize_Actual": lot_act,
        "ScrapQty": scrap,
        "YieldRate_pct": (lot_act - scrap) / lot_plan * 100,

        "Downtime_min": rng.poisson(5),
        "DowntimeReason": rng.choice(["MECH", "ELEC", "QC", "MATL", None], p=[.3, .2, .1, .1, .3]),
    })

# Build DataFrame
nal = pd.DataFrame(records)

# Dirty-data injection
nal.loc[rng.random(len(nal)) < 0.03, "OperatorID"] = None
nal.loc[rng.random(len(nal)) < 0.03, "RunTime_Actual_min"] = np.nan
nal.loc[rng.random(len(nal)) < 0.01, "RunTime_Actual_min"] *= 5
bad_col = random.choice([
    "SetupTime_Planned_min", "SetupTime_Actual_min",
    "RunTime_Planned_min",    "RunTime_Actual_min"
])
nal.loc[rng.random(len(nal)) < 0.01, bad_col] *= 60

# Maintenance injection
nal["MaintenanceFlag"] = 0
nal["MaintenanceType"] = None
unique_wcs = nal.WorkCenterID.unique()
for wc in unique_wcs:
    wc_df = nal[nal.WorkCenterID == wc]
    days = wc_df.RecordDateTime.dt.floor("D").drop_duplicates()
    pm_days = days.sample(frac=0.05, random_state=SEED)
    for day in pm_days:
        mask = (nal.WorkCenterID == wc) & (nal.RecordDateTime.dt.floor("D") == day)
        nal.loc[mask, ["MaintenanceFlag", "MaintenanceType", "Downtime_min"]] = [1, "PLANNED", 60]

# Output
Path("out").mkdir(exist_ok=True)
nal.sort_values("RecordDateTime").to_csv("out/NAL.csv", index=False)
print(f"✅ NAL.csv written | rows={len(nal):,} | glitch_col={bad_col}")
