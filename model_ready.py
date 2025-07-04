#!/usr/bin/env python

import pandas as pd
import numpy as np

# 1. Load your core NAL events (you already have PlantID, MachineClass, ProductComplexity)
df = pd.read_csv("out/NAL.csv", parse_dates=["RecordDateTime"])

# 2. Bring in order-level features (OrderDate, PlannedQty)
orders = pd.read_csv("out/production_orders.csv", parse_dates=["OrderDate"])
df = df.merge(
    orders[["ProductionOrderID","OrderDate","PlannedQty"]],
    on="ProductionOrderID",
    how="left"
)

# 3. Sanity check: these columns must now exist
#    • PlantID     (comes from NAL.csv)
#    • MachineClass (comes from NAL.csv)
#    • ProductComplexity (comes from NAL.csv)
#    • OrderDate, PlannedQty (we just merged)

missing = [c for c in ["PlantID","MachineClass","ProductComplexity","OrderDate","PlannedQty"] if c not in df.columns]
if missing:
    raise RuntimeError(f"Required columns missing: {missing}")

# 4. Feature engineering
df["Hour"]    = df.RecordDateTime.dt.hour
df["Weekday"] = df.RecordDateTime.dt.weekday
df["Month"]   = df.RecordDateTime.dt.month

# Additional time-based features
df["DayOfWeek"] = df.RecordDateTime.dt.day_name()
df["IsWeekend"] = df.RecordDateTime.dt.weekday.isin([5, 6]).astype(int)

# Shift classification
def classify_shift(hour):
    if 6 <= hour <= 14:
        return "DAY"
    elif 15 <= hour <= 22:
        return "EVENING"
    else:
        return "NIGHT"

df["Shift"] = df["Hour"].apply(classify_shift)

# Operational efficiency features
df["TotalOperationTime"] = df["SetupTime_Actual_min"] + df["RunTime_Actual_min"]
df["SetupEfficiency"] = df["SetupTime_Planned_min"] / df["SetupTime_Actual_min"]
df["RunEfficiency"] = df["RunTime_Planned_min"] / df["RunTime_Actual_min"]

# Lot size variance
df["LotSizeVariance"] = df["LotSize_Actual"] - df["LotSize_Planned"]
df["LotSizeVariancePct"] = (df["LotSizeVariance"] / df["LotSize_Planned"]) * 100

# Quality metrics
df["ScrapRate"] = (df["ScrapQty"] / df["LotSize_Actual"]) * 100
df["HasDowntime"] = (df["Downtime_min"] > 0).astype(int)
df["HasScrap"] = (df["ScrapQty"] > 0).astype(int)

# CAPACITY UTILIZATION FEATURES - Critical for production planning
# Work center capacity utilization
df["PlannedCapacityTime"] = df["SetupTime_Planned_min"] + df["RunTime_Planned_min"]
df["ActualCapacityTime"] = df["SetupTime_Actual_min"] + df["RunTime_Actual_min"]
df["CapacityUtilization"] = df["ActualCapacityTime"] / (df["ActualCapacityTime"] + df["Downtime_min"])

# Theoretical vs actual capacity consumption
df["TheoreticalCapacity"] = df["PlannedCapacityTime"] 
df["ActualCapacityConsumption"] = df["ActualCapacityTime"] + df["Downtime_min"]
df["CapacityOverrun"] = df["ActualCapacityConsumption"] - df["TheoreticalCapacity"]
df["CapacityOverrunPct"] = (df["CapacityOverrun"] / df["TheoreticalCapacity"]) * 100

# Production rate and throughput
df["ProductionRate"] = df["LotSize_Actual"] / df["ActualCapacityTime"]  # units per minute
df["PlannedProductionRate"] = df["LotSize_Planned"] / df["PlannedCapacityTime"]
df["ThroughputEfficiency"] = df["ProductionRate"] / df["PlannedProductionRate"]

# Bottleneck indicators
df["IsBottleneck"] = (df["CapacityUtilization"] > 0.85).astype(int)  # High utilization = potential bottleneck
df["CapacityStress"] = df["CapacityUtilization"] * df["ProductComplexity"].map({"LOW": 1, "MED": 1.5, "HIGH": 2})

# Keep raw data with outliers, missing values, and errors for realistic ML work
# This allows for proper data cleaning, outlier detection, and imputation practice

# 5. One-hot encode only the columns we know are present
df = pd.get_dummies(
    df,
    columns=["ProductComplexity","MachineClass","PlantID","Shift","DowntimeReason"],
    drop_first=True
)

# 6. (Optional) drop rows missing your target, if you like
df = df.dropna(subset=["RunTime_Actual_min"])

# 7. Persist the final model-ready table
df.to_csv("out/model_ready.csv", index=False)
print(f"model_ready.csv written | rows={len(df):,} | cols={df.shape[1]}")
