# comprehensive_eda.py - Cross-Dataset Analysis & Relationships

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.dates import DateFormatter
import warnings
warnings.filterwarnings('ignore')

# Configure plotting
plt.style.use('seaborn-v0_8')
sns.set_palette("husl")
plt.rcParams['figure.figsize'] = (15, 10)

print("="*80)
print("🔍 COMPREHENSIVE EDA: MANUFACTURING SYSTEM ANALYSIS")
print("="*80)

# Load all datasets
print("\n📁 LOADING ALL DATASETS...")
try:
    # Core datasets
    material_master = pd.read_csv("out/material_master.csv")
    bom_table = pd.read_csv("out/bom_table.csv")
    routing_table = pd.read_csv("out/routing_table.csv")
    production_orders = pd.read_csv("out/production_orders.csv", parse_dates=["OrderDate"])
    nal = pd.read_csv("out/NAL.csv", parse_dates=["RecordDateTime"])
    model_ready = pd.read_csv("out/model_ready.csv", parse_dates=["RecordDateTime"])
    
    print("✅ All datasets loaded successfully!")
    
    # Dataset overview
    datasets = {
        "Material Master": material_master,
        "BOM Table": bom_table,
        "Routing Table": routing_table,
        "Production Orders": production_orders,
        "NAL (Raw Events)": nal,
        "Model Ready": model_ready
    }
    
    print(f"\n📊 DATASET OVERVIEW:")
    for name, df in datasets.items():
        print(f"• {name}: {len(df):,} rows × {df.shape[1]} columns")
        
except FileNotFoundError as e:
    print(f"❌ Error loading datasets: {e}")
    exit(1)

print("\n" + "="*80)
print("🔗 DATASET RELATIONSHIPS & CONNECTIONS")
print("="*80)

# 1. MATERIAL MASTER ANALYSIS
print("\n1️⃣ MATERIAL MASTER HIERARCHY")
print("-" * 40)
material_counts = material_master['MaterialType'].value_counts()
complexity_dist = material_master.groupby(['MaterialType', 'ProductComplexity']).size().unstack(fill_value=0)

fig, axes = plt.subplots(1, 2, figsize=(15, 6))

# Material type distribution
axes[0].pie(material_counts.values, labels=material_counts.index, autopct='%1.1f%%', startangle=90)
axes[0].set_title('Material Type Distribution')

# Complexity by material type
complexity_dist.plot(kind='bar', ax=axes[1], stacked=True)
axes[1].set_title('Product Complexity by Material Type')
axes[1].set_xlabel('Material Type')
axes[1].set_ylabel('Count')
axes[1].legend(title='Complexity')
axes[1].tick_params(axis='x', rotation=45)

plt.tight_layout()
plt.show()

print(f"Material Types: {material_counts.to_dict()}")
print(f"Complexity Distribution:\n{complexity_dist}")

# 2. BOM RELATIONSHIPS
print("\n2️⃣ BILL OF MATERIALS (BOM) ANALYSIS")
print("-" * 40)

# BOM depth analysis
bom_stats = bom_table.groupby('ParentMaterial').agg({
    'ComponentMaterial': 'count',
    'Quantity': ['sum', 'mean']
}).round(2)
bom_stats.columns = ['Component_Count', 'Total_Qty', 'Avg_Qty_Per_Component']

# Find most complex products (most components)
top_complex = bom_stats.nlargest(10, 'Component_Count')
print("🔧 Most Complex Products (by component count):")
print(top_complex)

# BOM level analysis
level_analysis = bom_table.groupby('Level').agg({
    'ParentMaterial': 'nunique',
    'ComponentMaterial': 'nunique',
    'Quantity': ['sum', 'mean']
}).round(2)

print(f"\n📊 BOM Level Analysis:")
print(level_analysis)

# Visualize BOM complexity
plt.figure(figsize=(15, 6))

plt.subplot(1, 2, 1)
plt.hist(bom_stats['Component_Count'], bins=20, alpha=0.7, edgecolor='black')
plt.title('Distribution of Component Count per Product')
plt.xlabel('Number of Components')
plt.ylabel('Frequency')

plt.subplot(1, 2, 2)
level_counts = bom_table['Level'].value_counts().sort_index()
plt.bar(level_counts.index, level_counts.values, alpha=0.7)
plt.title('BOM Levels Distribution')
plt.xlabel('BOM Level')
plt.ylabel('Number of Relationships')

plt.tight_layout()
plt.show()

# 3. ROUTING & WORK CENTER ANALYSIS
print("\n3️⃣ ROUTING & WORK CENTER ANALYSIS")
print("-" * 40)

# Work center utilization across materials
wc_material_matrix = routing_table.pivot_table(
    index='WorkCenter', 
    columns='MaterialNumber', 
    values='OperationSeq', 
    aggfunc='count', 
    fill_value=0
)

print(f"Work Centers: {routing_table['WorkCenter'].nunique()}")
print(f"Materials with routings: {routing_table['MaterialNumber'].nunique()}")
print(f"Machine Classes: {routing_table['MachineClass'].nunique()}")

# Work center load analysis
wc_load = routing_table.groupby('WorkCenter').agg({
    'MaterialNumber': 'nunique',
    'SetupTime_min': 'mean',
    'RunTime_min': 'mean'
}).round(2)
wc_load['Total_Time'] = wc_load['SetupTime_min'] + wc_load['RunTime_min']
wc_load = wc_load.sort_values('Total_Time', ascending=False)

print(f"\n🏭 Work Center Load (Top 10):")
print(wc_load.head(10))

# Machine class distribution
machine_dist = routing_table.groupby('MachineClass').agg({
    'WorkCenter': 'nunique',
    'MaterialNumber': 'nunique',
    'SetupTime_min': 'mean',
    'RunTime_min': 'mean'
}).round(2)

plt.figure(figsize=(15, 10))

plt.subplot(2, 2, 1)
routing_table['MachineClass'].value_counts().plot(kind='bar', alpha=0.7)
plt.title('Operations by Machine Class')
plt.ylabel('Number of Operations')
plt.xticks(rotation=45)

plt.subplot(2, 2, 2)
plt.scatter(wc_load['SetupTime_min'], wc_load['RunTime_min'], alpha=0.7, s=50)
plt.xlabel('Average Setup Time (min)')
plt.ylabel('Average Run Time (min)')
plt.title('Work Center Setup vs Run Time')

plt.subplot(2, 2, 3)
ops_per_material = routing_table.groupby('MaterialNumber').size()
plt.hist(ops_per_material, bins=15, alpha=0.7, edgecolor='black')
plt.title('Operations per Material Distribution')
plt.xlabel('Number of Operations')
plt.ylabel('Frequency')

plt.subplot(2, 2, 4)
# Heatmap of work center usage
wc_usage = routing_table.groupby(['WorkCenter', 'MachineClass']).size().unstack(fill_value=0)
sns.heatmap(wc_usage, annot=True, fmt='d', cmap='YlOrRd', cbar_kws={'label': 'Operations'})
plt.title('Work Center × Machine Class Matrix')

plt.tight_layout()
plt.show()

# 4. PRODUCTION ORDERS ANALYSIS
print("\n4️⃣ PRODUCTION ORDERS ANALYSIS")
print("-" * 40)

# Order patterns
order_analysis = production_orders.groupby('MaterialNumber').agg({
    'ProductionOrderID': 'count',
    'PlannedQty': ['sum', 'mean'],
    'OrderDate': ['min', 'max']
}).round(2)
order_analysis.columns = ['Order_Count', 'Total_Planned_Qty', 'Avg_Planned_Qty', 'First_Order', 'Last_Order']

# Most ordered materials
top_ordered = order_analysis.nlargest(10, 'Order_Count')
print("📦 Most Frequently Ordered Materials:")
print(top_ordered[['Order_Count', 'Total_Planned_Qty', 'Avg_Planned_Qty']])

# Plant distribution
plant_orders = production_orders.groupby('PlantID').agg({
    'ProductionOrderID': 'count',
    'PlannedQty': 'sum',
    'MaterialNumber': 'nunique'
}).round(2)
plant_orders.columns = ['Order_Count', 'Total_Qty', 'Unique_Materials']

print(f"\n🏭 Plant Distribution:")
print(plant_orders)

# Time series analysis
monthly_orders = production_orders.set_index('OrderDate').resample('M').agg({
    'ProductionOrderID': 'count',
    'PlannedQty': 'sum'
})

plt.figure(figsize=(15, 8))

plt.subplot(2, 2, 1)
production_orders['PlantID'].value_counts().plot(kind='pie', autopct='%1.1f%%')
plt.title('Orders by Plant')

plt.subplot(2, 2, 2)
monthly_orders['ProductionOrderID'].plot(kind='line', marker='o')
plt.title('Monthly Order Count Trend')
plt.ylabel('Number of Orders')
plt.xticks(rotation=45)

plt.subplot(2, 2, 3)
plt.hist(production_orders['PlannedQty'], bins=30, alpha=0.7, edgecolor='black')
plt.title('Planned Quantity Distribution')
plt.xlabel('Planned Quantity')
plt.ylabel('Frequency')

plt.subplot(2, 2, 4)
complexity_orders = production_orders.merge(material_master[['MaterialNumber', 'ProductComplexity']], on='MaterialNumber')
complexity_orders.groupby('ProductComplexity')['PlannedQty'].sum().plot(kind='bar', alpha=0.7)
plt.title('Total Planned Quantity by Complexity')
plt.ylabel('Total Planned Quantity')
plt.xticks(rotation=0)

plt.tight_layout()
plt.show()

# 5. CROSS-DATASET RELATIONSHIPS
print("\n5️⃣ CROSS-DATASET RELATIONSHIPS")
print("-" * 40)

# Material complexity vs operations
material_operations = routing_table.groupby('MaterialNumber').size().reset_index(name='Operation_Count')
material_complexity = material_master[['MaterialNumber', 'ProductComplexity']].copy()
complexity_ops = material_complexity.merge(material_operations, on='MaterialNumber', how='left')
complexity_ops['Operation_Count'] = complexity_ops['Operation_Count'].fillna(0)

complexity_vs_ops = complexity_ops.groupby('ProductComplexity')['Operation_Count'].agg(['mean', 'std', 'count']).round(2)
print("🔧 Product Complexity vs Average Operations:")
print(complexity_vs_ops)

# Plant vs Material Type analysis
plant_materials = production_orders.merge(material_master[['MaterialNumber', 'MaterialType']], on='MaterialNumber')
plant_type_matrix = plant_materials.pivot_table(
    index='PlantID', 
    columns='MaterialType', 
    values='ProductionOrderID', 
    aggfunc='count', 
    fill_value=0
)

print(f"\n🏭 Plant × Material Type Matrix:")
print(plant_type_matrix)

# 6. OPERATIONAL PERFORMANCE ANALYSIS
print("\n6️⃣ OPERATIONAL PERFORMANCE ANALYSIS")
print("-" * 40)

# NAL vs Model Ready comparison
print(f"NAL Records: {len(nal):,}")
print(f"Model Ready Records: {len(model_ready):,}")
print(f"Data Retention Rate: {len(model_ready)/len(nal)*100:.1f}%")

# Performance metrics by work center
if 'WorkCenterID' in model_ready.columns:
    wc_performance = model_ready.groupby('WorkCenterID').agg({
        'SetupTime_Actual_min': 'mean',
        'RunTime_Actual_min': 'mean',
        'YieldRate_pct': 'mean',
        'CapacityUtilization': 'mean',
        'Downtime_min': 'mean'
    }).round(2)
    
    print(f"\n⚡ Work Center Performance (Top 10 by Capacity Utilization):")
    print(wc_performance.sort_values('CapacityUtilization', ascending=False).head(10))

# Material complexity impact on performance
if 'ProductComplexity_LOW' in model_ready.columns and 'ProductComplexity_MED' in model_ready.columns:
    # Derive complexity from one-hot encoding
    model_ready_complexity = model_ready.copy()
    model_ready_complexity['ProductComplexity'] = 'HIGH'  # Default
    model_ready_complexity.loc[model_ready_complexity['ProductComplexity_LOW'] == True, 'ProductComplexity'] = 'LOW'
    model_ready_complexity.loc[model_ready_complexity['ProductComplexity_MED'] == True, 'ProductComplexity'] = 'MED'
    
    complexity_performance = model_ready_complexity.groupby('ProductComplexity').agg({
        'SetupTime_Actual_min': 'mean',
        'RunTime_Actual_min': 'mean',
        'YieldRate_pct': 'mean',
        'CapacityUtilization': 'mean',
        'ThroughputEfficiency': 'mean'
    }).round(2)
    
    print(f"\n🎯 Performance by Product Complexity:")
    print(complexity_performance)

# 7. ADVANCED VISUALIZATIONS
print("\n7️⃣ ADVANCED RELATIONSHIP VISUALIZATIONS")
print("-" * 40)

# Create comprehensive dashboard
fig = plt.figure(figsize=(20, 16))

# Material flow diagram (simplified)
plt.subplot(3, 4, 1)
material_flow = material_master['MaterialType'].value_counts()
plt.pie(material_flow.values, labels=material_flow.index, autopct='%1.0f', startangle=90)
plt.title('Material Hierarchy')

# BOM complexity heatmap
plt.subplot(3, 4, 2)
bom_level_qty = bom_table.pivot_table(index='Level', columns='ParentMaterial', values='Quantity', aggfunc='sum', fill_value=0)
# Take top 20 materials for visibility
top_materials = bom_stats.nlargest(20, 'Component_Count').index
bom_subset = bom_level_qty[bom_level_qty.columns.intersection(top_materials)]
if not bom_subset.empty:
    sns.heatmap(bom_subset, cmap='YlOrRd', cbar_kws={'label': 'Total Quantity'})
plt.title('BOM Quantity by Level (Top Materials)')

# Work center network
plt.subplot(3, 4, 3)
wc_material_count = routing_table.groupby('WorkCenter')['MaterialNumber'].nunique().sort_values(ascending=False)
wc_material_count.head(15).plot(kind='barh', alpha=0.7)
plt.title('Materials per Work Center')
plt.xlabel('Number of Materials')

# Plant capacity distribution
plt.subplot(3, 4, 4)
if 'PlantID_PLT2' in model_ready.columns and 'PlantID_PLT3' in model_ready.columns:
    # Derive plant from one-hot
    model_ready_plants = model_ready.copy()
    model_ready_plants['PlantID'] = 'PLT1'  # Default
    model_ready_plants.loc[model_ready_plants['PlantID_PLT2'] == True, 'PlantID'] = 'PLT2'
    model_ready_plants.loc[model_ready_plants['PlantID_PLT3'] == True, 'PlantID'] = 'PLT3'
    
    plant_capacity = model_ready_plants.groupby('PlantID')['CapacityUtilization'].mean()
    plant_capacity.plot(kind='bar', alpha=0.7, color=['#1f77b4', '#ff7f0e', '#2ca02c'])
    plt.title('Average Capacity Utilization by Plant')
    plt.ylabel('Capacity Utilization')
    plt.xticks(rotation=0)

# Time series correlation
plt.subplot(3, 4, 5)
if 'RecordDateTime' in model_ready.columns:
    daily_metrics = model_ready.set_index('RecordDateTime').resample('D').agg({
        'CapacityUtilization': 'mean',
        'YieldRate_pct': 'mean'
    }).dropna()
    
    if len(daily_metrics) > 10:
        plt.scatter(daily_metrics['CapacityUtilization'], daily_metrics['YieldRate_pct'], alpha=0.6)
        plt.xlabel('Daily Avg Capacity Utilization')
        plt.ylabel('Daily Avg Yield Rate')
        plt.title('Capacity vs Quality Relationship')

# Machine class efficiency
plt.subplot(3, 4, 6)
if any(col.startswith('MachineClass_') for col in model_ready.columns):
    machine_cols = [col for col in model_ready.columns if col.startswith('MachineClass_')]
    machine_efficiency = {}
    for col in machine_cols:
        machine_name = col.replace('MachineClass_', '')
        machine_data = model_ready[model_ready[col] == True]
        if len(machine_data) > 0:
            machine_efficiency[machine_name] = machine_data['ThroughputEfficiency'].mean()
    
    # Add CNC (assumed remaining)
    cnc_data = model_ready[~model_ready[machine_cols].any(axis=1)]
    if len(cnc_data) > 0:
        machine_efficiency['CNC'] = cnc_data['ThroughputEfficiency'].mean()
    
    if machine_efficiency:
        plt.bar(machine_efficiency.keys(), machine_efficiency.values(), alpha=0.7)
        plt.title('Throughput Efficiency by Machine Class')
        plt.ylabel('Average Efficiency')
        plt.xticks(rotation=45)

# Order fulfillment timeline
plt.subplot(3, 4, 7)
monthly_production = model_ready.set_index('RecordDateTime').resample('M').size()
monthly_orders['ProductionOrderID'].plot(kind='line', marker='o', label='Orders', alpha=0.7)
if len(monthly_production) > 0:
    monthly_production.plot(kind='line', marker='s', label='Production Events', alpha=0.7)
plt.title('Orders vs Production Timeline')
plt.ylabel('Count')
plt.legend()
plt.xticks(rotation=45)

# Bottleneck analysis
plt.subplot(3, 4, 8)
if 'IsBottleneck' in model_ready.columns:
    bottleneck_by_wc = model_ready.groupby('WorkCenterID')['IsBottleneck'].mean().sort_values(ascending=False)
    bottleneck_by_wc.head(10).plot(kind='bar', alpha=0.7, color='red')
    plt.title('Bottleneck Rate by Work Center')
    plt.ylabel('Bottleneck Rate')
    plt.xticks(rotation=45)

# Quality vs complexity
plt.subplot(3, 4, 9)
if 'ProductComplexity' in locals():
    complexity_quality = model_ready_complexity.groupby('ProductComplexity').agg({
        'YieldRate_pct': 'mean',
        'ScrapRate': 'mean'
    })
    complexity_quality.plot(kind='bar', alpha=0.7)
    plt.title('Quality Metrics by Complexity')
    plt.ylabel('Rate')
    plt.xticks(rotation=0)
    plt.legend()

# Setup vs Run efficiency correlation
plt.subplot(3, 4, 10)
plt.scatter(model_ready['SetupEfficiency'], model_ready['RunEfficiency'], alpha=0.5, s=20)
plt.xlabel('Setup Efficiency')
plt.ylabel('Run Efficiency')
plt.title('Setup vs Run Efficiency')

# Capacity stress distribution
plt.subplot(3, 4, 11)
if 'CapacityStress' in model_ready.columns:
    plt.hist(model_ready['CapacityStress'], bins=30, alpha=0.7, edgecolor='black')
    plt.title('Capacity Stress Distribution')
    plt.xlabel('Capacity Stress Level')
    plt.ylabel('Frequency')

# Network complexity
plt.subplot(3, 4, 12)
# Material-WorkCenter network density
material_wc_pairs = model_ready.groupby(['MaterialNumber', 'WorkCenterID']).size().reset_index(name='Operations')
network_density = len(material_wc_pairs) / (model_ready['MaterialNumber'].nunique() * model_ready['WorkCenterID'].nunique())
plt.text(0.5, 0.5, f'Manufacturing\\nNetwork Density\\n{network_density:.3f}', 
         ha='center', va='center', fontsize=14, 
         bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.8))
plt.xlim(0, 1)
plt.ylim(0, 1)
plt.axis('off')
plt.title('System Complexity Metric')

plt.tight_layout()
plt.show()

# 8. SUMMARY INSIGHTS
print("\n" + "="*80)
print("📊 MANUFACTURING SYSTEM INSIGHTS SUMMARY")
print("="*80)

print(f"""
🏭 SYSTEM OVERVIEW:
• Materials: {material_master['MaterialNumber'].nunique()} total ({material_counts.to_dict()})
• Work Centers: {routing_table['WorkCenter'].nunique()}
• Machine Classes: {routing_table['MachineClass'].nunique()}
• Plants: {production_orders['PlantID'].nunique()}
• Production Orders: {len(production_orders):,}
• Operations Recorded: {len(model_ready):,}

🔗 RELATIONSHIPS:
• BOM Relationships: {len(bom_table):,}
• Routing Operations: {len(routing_table):,}
• Network Density: {network_density:.3f}
• Average Components per Product: {bom_stats['Component_Count'].mean():.1f}

📈 PERFORMANCE:
• Average Capacity Utilization: {model_ready['CapacityUtilization'].mean():.1%}
• Average Yield Rate: {model_ready['YieldRate_pct'].mean():.1f}%
• Data Processing Efficiency: {len(model_ready)/len(nal)*100:.1f}%
""")

if 'bottleneck_by_wc' in locals():
    print(f"• Top Bottleneck Work Center: {bottleneck_by_wc.index[0]} ({bottleneck_by_wc.iloc[0]:.1%})")

print(f"""
🎯 KEY FINDINGS:
• Most Complex Material: {top_complex.index[0]} ({top_complex.iloc[0, 0]} components)
• Busiest Work Center: {wc_load.index[0]} ({wc_load.iloc[0, 0]} materials)
• Most Ordered Material: {top_ordered.index[0]} ({top_ordered.iloc[0, 0]} orders)
""")

print("="*80)
print("✅ COMPREHENSIVE EDA COMPLETED!")
print("="*80)
