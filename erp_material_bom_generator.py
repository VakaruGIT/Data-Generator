# erp_material_bom_generator.py

import numpy as np, pandas as pd, random
from faker import Faker
from pathlib import Path
from datetime import datetime, timedelta

SEED = 42
NUM_FG = 30
NUM_SFG = 60
NUM_RAW = 300
NUM_ORDERS = 5000
faker = Faker()
random.seed(SEED)
np.random.seed(SEED)
rng = np.random.default_rng(SEED)

MACH_CLASSES = ["CNC", "PRESS", "MILL", "ROBOT", "GRIND"]
PARTS = [
    "Engine Block", "Crankshaft", "Camshaft", "Gearbox", "Drive Shaft", "Differential",
    "Turbocharger", "Radiator", "Oil Pump", "Water Pump", "Fuel Injector", "Clutch Plate",
    "Brake Disc", "Caliper", "Sway Bar", "Control Arm", "Steering Knuckle", "Shock Absorber",
    "Exhaust Manifold", "Catalytic Converter", "ECU", "Instrument Cluster", "Airbag Module",
    "Timing Belt", "Fan", "Sensor", "Bracket", "Bearing", "Seal"]
BRANDS = [
    "Bosch", "Delphi", "Denso", "Valeo", "Magneti Marelli", "ACDelco", "TRW", "Continental",
    "OEM", "Genuine", "Aftermarket", "Remanufactured", "Performance", "HD", "Sport"]

def part_name():
    return f"{random.choice(BRANDS)} {random.choice(PARTS)}"

def generate_material_master():
    rows = []
    for i in range(NUM_FG):
        rows.append({"MaterialNumber": f"FG{i+1:04}", "MaterialType": "FG",
                     "MaterialName": part_name(),
                     "ProductComplexity": rng.choice(["LOW","MED","HIGH"], p=[0.4,0.4,0.2])})
    for i in range(NUM_SFG):
        rows.append({"MaterialNumber": f"SFG{i+1:04}", "MaterialType": "SFG",
                     "MaterialName": part_name(),
                     "ProductComplexity": rng.choice(["LOW","MED","HIGH"], p=[0.6,0.3,0.1])})
    for i in range(NUM_RAW):
        rows.append({"MaterialNumber": f"RAW{i+1:04}", "MaterialType": "RAW",
                     "MaterialName": part_name(), "ProductComplexity": "LOW"})
    return pd.DataFrame(rows)

def generate_bom(materials):
    bom_rows = []
    fg_list = materials[materials.MaterialType=="FG"]["MaterialNumber"].tolist()
    sfg_list = materials[materials.MaterialType=="SFG"]["MaterialNumber"].tolist()
    raw_list = materials[materials.MaterialType=="RAW"]["MaterialNumber"].tolist()
    for fg in fg_list:
        sfg_used = rng.choice(sfg_list, size=rng.integers(2, 5), replace=False)
        for sfg in sfg_used:
            qty = rng.integers(1, 4)
            bom_rows.append({"ParentMaterial": fg, "ComponentMaterial": sfg,
                             "Quantity": qty, "Level": 1})
    for sfg in sfg_list:
        raw_used = rng.choice(raw_list, size=rng.integers(3, 8), replace=False)
        for raw in raw_used:
            qty = rng.integers(1, 10)
            bom_rows.append({"ParentMaterial": sfg, "ComponentMaterial": raw,
                             "Quantity": qty, "Level": 2})
    return pd.DataFrame(bom_rows)

def generate_production_orders(materials, n_orders=NUM_ORDERS):
    fg_list = materials[materials.MaterialType=="FG"]
    recs = []
    start_date = datetime(2025, 1, 1)
    for i in range(n_orders):
        fg = fg_list.sample(1).iloc[0]
        recs.append({
            "ProductionOrderID": f"PO{100000+i}",
            "MaterialNumber": fg["MaterialNumber"],
            "MaterialName": fg["MaterialName"],
            "ProductComplexity": fg["ProductComplexity"],
            "OrderDate": start_date + timedelta(days=int(rng.integers(0, 365))),
            "PlannedQty": int(rng.integers(10, 200)),
            "MachineClass": rng.choice(MACH_CLASSES),
            "PlantID": rng.choice(["PLT1","PLT2","PLT3"])
        })
    return pd.DataFrame(recs)

if __name__ == "__main__":
    Path("out").mkdir(exist_ok=True)
    mm = generate_material_master()
    bom = generate_bom(mm)
    orders = generate_production_orders(mm)
    mm.to_csv("out/material_master.csv", index=False)
    bom.to_csv("out/bom_table.csv", index=False)
    orders.to_csv("out/production_orders.csv", index=False)
    print("✅ Generated:")
    print(f"• material_master.csv   → {len(mm):,} rows")
    print(f"• bom_table.csv         → {len(bom):,} rows")
    print(f"• production_orders.csv → {len(orders):,} rows")
