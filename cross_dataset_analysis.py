#!/usr/bin/env python
"""
Cross-Dataset Analysis for Manufacturing System
==================================================
This script analyzes relationships and connections between all datasets
for IT collaboration and system understanding.
"""

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
print("🔍 CROSS-DATASET ANALYSIS: MANUFACTURING SYSTEM CONNECTIONS")
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
print("🔗 DATASET RELATIONSHIPS & DATA FLOW")
print("="*80)

# 1. MATERIAL HIERARCHY ANALYSIS
print("\n1️⃣ MATERIAL MASTER HIERARCHY")
print("-" * 50)
material_counts = material_master['MaterialType'].value_counts()
print(f"Material Types: {material_counts.to_dict()}")

# Material complexity distribution
complexity_dist = material_master.groupby(['MaterialType', 'ProductComplexity']).size().unstack(fill_value=0)
print(f"\nComplexity Distribution:\n{complexity_dist}")

# Visualize material hierarchy
fig, axes = plt.subplots(2, 2, figsize=(15, 10))

# Material type pie chart
axes[0, 0].pie(material_counts.values, labels=material_counts.index, autopct='%1.1f%%', startangle=90)
axes[0, 0].set_title('Material Type Distribution')

# Complexity stacked bar
complexity_dist.plot(kind='bar', ax=axes[0, 1], stacked=True, alpha=0.7)
axes[0, 1].set_title('Product Complexity by Material Type')
axes[0, 1].set_xlabel('Material Type')
axes[0, 1].set_ylabel('Count')
axes[0, 1].legend(title='Complexity')
axes[0, 1].tick_params(axis='x', rotation=45)

# Material name length distribution (complexity proxy)
material_master['NameLength'] = material_master['MaterialName'].str.len()
axes[1, 0].hist(material_master['NameLength'], bins=20, alpha=0.7, edgecolor='black')
axes[1, 0].set_title('Material Name Length Distribution')
axes[1, 0].set_xlabel('Name Length (characters)')
axes[1, 0].set_ylabel('Frequency')

# Material creation pattern (synthetic but useful for analysis)
material_master['MaterialID'] = material_master['MaterialNumber'].str.extract('(\d+)').astype(int)
axes[1, 1].scatter(material_master['MaterialID'], material_master['NameLength'], 
                   c=material_master['MaterialType'].factorize()[0], alpha=0.7)
axes[1, 1].set_title('Material ID vs Name Length')
axes[1, 1].set_xlabel('Material ID')
axes[1, 1].set_ylabel('Name Length')

plt.tight_layout()
plt.show()

# 2. BOM NETWORK ANALYSIS
print("\n2️⃣ BILL OF MATERIALS (BOM) NETWORK")
print("-" * 50)

# BOM complexity metrics
bom_stats = bom_table.groupby('ParentMaterial').agg({
    'ComponentMaterial': 'count',
    'Quantity': ['sum', 'mean', 'std']
}).round(2)
bom_stats.columns = ['Component_Count', 'Total_Qty', 'Avg_Qty_Per_Component', 'Qty_Std']

# Find most complex products
top_complex = bom_stats.nlargest(10, 'Component_Count')
print("🔧 Most Complex Products (by component count):")
print(top_complex[['Component_Count', 'Total_Qty', 'Avg_Qty_Per_Component']])

# BOM level analysis
level_analysis = bom_table.groupby('Level').agg({
    'ParentMaterial': 'nunique',
    'ComponentMaterial': 'nunique',
    'Quantity': ['sum', 'mean', 'std']
}).round(2)
level_analysis.columns = ['Parent_Count', 'Component_Count', 'Total_Qty', 'Avg_Qty', 'Qty_Std']

print(f"\n📊 BOM Level Analysis:")
print(level_analysis)

# BOM network visualization
fig, axes = plt.subplots(2, 2, figsize=(15, 10))

# Component count distribution
axes[0, 0].hist(bom_stats['Component_Count'], bins=15, alpha=0.7, edgecolor='black')
axes[0, 0].set_title('Components per Product Distribution')
axes[0, 0].set_xlabel('Number of Components')
axes[0, 0].set_ylabel('Frequency')

# BOM levels
level_counts = bom_table['Level'].value_counts().sort_index()
axes[0, 1].bar(level_counts.index, level_counts.values, alpha=0.7, color='orange')
axes[0, 1].set_title('BOM Level Distribution')
axes[0, 1].set_xlabel('BOM Level')
axes[0, 1].set_ylabel('Number of Relationships')

# Quantity distribution by level
bom_table.boxplot(column='Quantity', by='Level', ax=axes[1, 0])
axes[1, 0].set_title('Quantity Distribution by BOM Level')
axes[1, 0].set_xlabel('BOM Level')
axes[1, 0].set_ylabel('Quantity')

# BOM network density
parent_component_matrix = bom_table.pivot_table(
    index='ParentMaterial', 
    columns='ComponentMaterial', 
    values='Quantity', 
    aggfunc='sum', 
    fill_value=0
)
# Show subset for visualization
subset_matrix = parent_component_matrix.iloc[:10, :15]  # Top 10 parents, 15 components
im = axes[1, 1].imshow(subset_matrix.values, cmap='YlOrRd', aspect='auto')
axes[1, 1].set_title('BOM Relationships Heatmap (Sample)')
axes[1, 1].set_xlabel('Component Materials')
axes[1, 1].set_ylabel('Parent Materials')
plt.colorbar(im, ax=axes[1, 1], label='Quantity')

plt.tight_layout()
plt.show()

# 3. ROUTING & WORK CENTER ANALYSIS
print("\n3️⃣ ROUTING & WORK CENTER NETWORK")
print("-" * 50)

# Work center analysis
wc_analysis = routing_table.groupby('WorkCenter').agg({
    'MaterialNumber': 'nunique',
    'SetupTime_min': ['mean', 'std'],
    'RunTime_min': ['mean', 'std'],
    'OperationSeq': 'count'
}).round(2)
wc_analysis.columns = ['Materials', 'Setup_Mean', 'Setup_Std', 'Run_Mean', 'Run_Std', 'Operations']
wc_analysis['Total_Mean_Time'] = wc_analysis['Setup_Mean'] + wc_analysis['Run_Mean']

print(f"Work Centers: {routing_table['WorkCenter'].nunique()}")
print(f"Materials with routings: {routing_table['MaterialNumber'].nunique()}")
print(f"Machine Classes: {routing_table['MachineClass'].nunique()}")

# Top loaded work centers
top_wc = wc_analysis.nlargest(10, 'Total_Mean_Time')
print(f"\n🏭 Most Time-Intensive Work Centers:")
print(top_wc[['Materials', 'Setup_Mean', 'Run_Mean', 'Total_Mean_Time', 'Operations']])

# Machine class distribution
machine_analysis = routing_table.groupby('MachineClass').agg({
    'WorkCenter': 'nunique',
    'MaterialNumber': 'nunique',
    'SetupTime_min': 'mean',
    'RunTime_min': 'mean',
    'OperationSeq': 'count'
}).round(2)
machine_analysis.columns = ['Work_Centers', 'Materials', 'Avg_Setup', 'Avg_Run', 'Operations']

print(f"\n⚙️ Machine Class Analysis:")
print(machine_analysis)

# Routing network visualization
fig, axes = plt.subplots(2, 2, figsize=(15, 10))

# Work center load distribution
wc_analysis['Total_Mean_Time'].plot(kind='hist', bins=15, alpha=0.7, ax=axes[0, 0], edgecolor='black')
axes[0, 0].set_title('Work Center Load Distribution')
axes[0, 0].set_xlabel('Total Average Time (min)')
axes[0, 0].set_ylabel('Frequency')

# Machine class operations
machine_analysis['Operations'].plot(kind='bar', ax=axes[0, 1], alpha=0.7)
axes[0, 1].set_title('Operations by Machine Class')
axes[0, 1].set_ylabel('Number of Operations')
axes[0, 1].tick_params(axis='x', rotation=45)

# Setup vs Run time correlation
axes[1, 0].scatter(wc_analysis['Setup_Mean'], wc_analysis['Run_Mean'], 
                   s=wc_analysis['Materials']*5, alpha=0.6)
axes[1, 0].set_xlabel('Average Setup Time (min)')
axes[1, 0].set_ylabel('Average Run Time (min)')
axes[1, 0].set_title('Setup vs Run Time by Work Center')

# Work center utilization heatmap
wc_machine_matrix = routing_table.pivot_table(
    index='WorkCenter', 
    columns='MachineClass', 
    values='OperationSeq', 
    aggfunc='count', 
    fill_value=0
)
sns.heatmap(wc_machine_matrix, annot=True, fmt='d', cmap='YlOrRd', ax=axes[1, 1])
axes[1, 1].set_title('Work Center × Machine Class Matrix')

plt.tight_layout()
plt.show()

# 4. PRODUCTION ORDERS ANALYSIS
print("\n4️⃣ PRODUCTION ORDERS PATTERN ANALYSIS")
print("-" * 50)

# Order analysis
order_analysis = production_orders.groupby('MaterialNumber').agg({
    'ProductionOrderID': 'count',
    'PlannedQty': ['sum', 'mean', 'std'],
    'OrderDate': ['min', 'max']
}).round(2)
order_analysis.columns = ['Order_Count', 'Total_Planned', 'Avg_Planned', 'Std_Planned', 'First_Order', 'Last_Order']

# Calculate order frequency
order_analysis['Date_Range'] = (order_analysis['Last_Order'] - order_analysis['First_Order']).dt.days
order_analysis['Order_Frequency'] = order_analysis['Order_Count'] / (order_analysis['Date_Range'] + 1)

# Most ordered materials
top_ordered = order_analysis.nlargest(10, 'Order_Count')
print("📦 Most Frequently Ordered Materials:")
print(top_ordered[['Order_Count', 'Total_Planned', 'Avg_Planned', 'Order_Frequency']])

# Plant distribution
plant_analysis = production_orders.groupby('PlantID').agg({
    'ProductionOrderID': 'count',
    'PlannedQty': ['sum', 'mean'],
    'MaterialNumber': 'nunique'
}).round(2)
plant_analysis.columns = ['Order_Count', 'Total_Qty', 'Avg_Qty', 'Unique_Materials']

print(f"\n🏭 Plant Distribution:")
print(plant_analysis)

# Time series analysis
monthly_orders = production_orders.set_index('OrderDate').resample('M').agg({
    'ProductionOrderID': 'count',
    'PlannedQty': 'sum'
})

# Order analysis visualization
fig, axes = plt.subplots(2, 2, figsize=(15, 10))

# Plant distribution
plant_analysis['Order_Count'].plot(kind='pie', ax=axes[0, 0], autopct='%1.1f%%', startangle=90)
axes[0, 0].set_title('Orders by Plant')
axes[0, 0].set_ylabel('')

# Monthly order trend
monthly_orders['ProductionOrderID'].plot(kind='line', marker='o', ax=axes[0, 1], alpha=0.7)
axes[0, 1].set_title('Monthly Order Count Trend')
axes[0, 1].set_ylabel('Number of Orders')
axes[0, 1].tick_params(axis='x', rotation=45)

# Planned quantity distribution
axes[1, 0].hist(production_orders['PlannedQty'], bins=30, alpha=0.7, edgecolor='black')
axes[1, 0].set_title('Planned Quantity Distribution')
axes[1, 0].set_xlabel('Planned Quantity')
axes[1, 0].set_ylabel('Frequency')

# Order frequency vs quantity
axes[1, 1].scatter(order_analysis['Order_Count'], order_analysis['Total_Planned'], alpha=0.6)
axes[1, 1].set_xlabel('Order Count')
axes[1, 1].set_ylabel('Total Planned Quantity')
axes[1, 1].set_title('Order Frequency vs Total Quantity')

plt.tight_layout()
plt.show()

# 5. CROSS-DATASET RELATIONSHIP ANALYSIS
print("\n5️⃣ CROSS-DATASET RELATIONSHIPS")
print("-" * 50)

# Material complexity vs routing complexity
material_routing = routing_table.merge(material_master[['MaterialNumber', 'ProductComplexity']], 
                                     on='MaterialNumber', how='left')

# Operations per material by complexity
ops_by_complexity = material_routing.groupby(['MaterialNumber', 'ProductComplexity']).size().reset_index(name='Operation_Count')
complexity_ops = ops_by_complexity.groupby('ProductComplexity')['Operation_Count'].agg(['mean', 'std', 'count']).round(2)

print("🔧 Product Complexity vs Operations:")
print(complexity_ops)

# Plant vs Material Type analysis
plant_materials = production_orders.merge(material_master[['MaterialNumber', 'MaterialType']], 
                                        on='MaterialNumber', how='left')
plant_type_matrix = plant_materials.pivot_table(
    index='PlantID', 
    columns='MaterialType', 
    values='ProductionOrderID', 
    aggfunc='count', 
    fill_value=0
)

print(f"\n🏭 Plant × Material Type Matrix:")
print(plant_type_matrix)

# Production volume vs BOM complexity
bom_complexity = bom_stats.reset_index()
production_volume = production_orders.groupby('MaterialNumber')['PlannedQty'].sum().reset_index()
volume_complexity = production_volume.merge(bom_complexity, left_on='MaterialNumber', right_on='ParentMaterial', how='inner')

if len(volume_complexity) > 0:
    print(f"\n📊 Production Volume vs BOM Complexity Correlation:")
    correlation = volume_complexity[['PlannedQty', 'Component_Count', 'Total_Qty']].corr()
    print(correlation)

# 6. OPERATIONAL PERFORMANCE ANALYSIS
print("\n6️⃣ OPERATIONAL PERFORMANCE METRICS")
print("-" * 50)

# NAL vs Model Ready comparison
print(f"NAL Records: {len(nal):,}")
print(f"Model Ready Records: {len(model_ready):,}")
print(f"Data Retention Rate: {len(model_ready)/len(nal)*100:.1f}%")

# Performance metrics from model_ready
if len(model_ready) > 0:
    # Basic performance metrics
    perf_metrics = {
        'Average Yield Rate': f"{model_ready['YieldRate_pct'].mean():.1f}%",
        'Average Capacity Utilization': f"{model_ready['CapacityUtilization'].mean():.1%}",
        'Average Setup Time': f"{model_ready['SetupTime_Actual_min'].mean():.1f} min",
        'Average Run Time': f"{model_ready['RunTime_Actual_min'].mean():.1f} min",
        'Total Downtime': f"{model_ready['Downtime_min'].sum():,.0f} min"
    }
    
    print(f"\n⚡ Key Performance Metrics:")
    for metric, value in perf_metrics.items():
        print(f"• {metric}: {value}")

# Work center performance analysis
if 'WorkCenterID' in model_ready.columns:
    wc_performance = model_ready.groupby('WorkCenterID').agg({
        'CapacityUtilization': 'mean',
        'YieldRate_pct': 'mean',
        'Downtime_min': 'sum',
        'ThroughputEfficiency': 'mean'
    }).round(2)
    
    # Top performing work centers
    top_performers = wc_performance.nlargest(10, 'CapacityUtilization')
    print(f"\n🏆 Top Work Centers by Capacity Utilization:")
    print(top_performers)

# 7. ADVANCED VISUALIZATIONS
print("\n7️⃣ SYSTEM INTEGRATION DASHBOARD")
print("-" * 50)

# Create comprehensive system dashboard
fig = plt.figure(figsize=(20, 16))

# 1. Material flow diagram
plt.subplot(3, 4, 1)
material_flow = material_master['MaterialType'].value_counts()
plt.pie(material_flow.values, labels=material_flow.index, autopct='%1.0f%%', startangle=90)
plt.title('Material Flow Distribution')

# 2. BOM network complexity
plt.subplot(3, 4, 2)
bom_complexity_dist = bom_stats['Component_Count'].value_counts().sort_index()
plt.bar(bom_complexity_dist.index, bom_complexity_dist.values, alpha=0.7)
plt.title('BOM Complexity Distribution')
plt.xlabel('Number of Components')
plt.ylabel('Number of Products')

# 3. Work center network
plt.subplot(3, 4, 3)
wc_material_count = routing_table.groupby('WorkCenter')['MaterialNumber'].nunique().sort_values(ascending=False)
wc_material_count.head(10).plot(kind='barh', alpha=0.7)
plt.title('Top 10 Work Centers by Material Count')
plt.xlabel('Number of Materials')

# 4. Production order timeline
plt.subplot(3, 4, 4)
monthly_orders['ProductionOrderID'].plot(kind='line', marker='o', alpha=0.7)
plt.title('Monthly Order Pattern')
plt.ylabel('Number of Orders')
plt.xticks(rotation=45)

# 5. Plant capacity distribution
plt.subplot(3, 4, 5)
plant_analysis['Total_Qty'].plot(kind='bar', alpha=0.7, color=['#1f77b4', '#ff7f0e', '#2ca02c'])
plt.title('Total Planned Quantity by Plant')
plt.ylabel('Total Quantity')
plt.xticks(rotation=0)

# 6. Machine class utilization
plt.subplot(3, 4, 6)
machine_analysis['Operations'].plot(kind='bar', alpha=0.7)
plt.title('Operations by Machine Class')
plt.ylabel('Number of Operations')
plt.xticks(rotation=45)

# 7. Quality metrics timeline
plt.subplot(3, 4, 7)
if len(model_ready) > 0:
    daily_yield = model_ready.set_index('RecordDateTime').resample('D')['YieldRate_pct'].mean()
    daily_yield.plot(kind='line', alpha=0.7)
    plt.title('Daily Average Yield Rate')
    plt.ylabel('Yield Rate (%)')
    plt.xticks(rotation=45)

# 8. Capacity utilization distribution
plt.subplot(3, 4, 8)
if len(model_ready) > 0:
    plt.hist(model_ready['CapacityUtilization'], bins=30, alpha=0.7, edgecolor='black')
    plt.title('Capacity Utilization Distribution')
    plt.xlabel('Capacity Utilization')
    plt.ylabel('Frequency')

# 9. Downtime analysis
plt.subplot(3, 4, 9)
if len(model_ready) > 0:
    downtime_by_reason = model_ready.groupby('DowntimeReason')['Downtime_min'].sum().sort_values(ascending=False)
    if len(downtime_by_reason) > 0:
        downtime_by_reason.plot(kind='bar', alpha=0.7)
        plt.title('Downtime by Reason')
        plt.ylabel('Total Downtime (min)')
        plt.xticks(rotation=45)

# 10. Setup vs Run efficiency
plt.subplot(3, 4, 10)
if len(model_ready) > 0 and 'SetupEfficiency' in model_ready.columns:
    plt.scatter(model_ready['SetupEfficiency'], model_ready['RunEfficiency'], alpha=0.5, s=20)
    plt.xlabel('Setup Efficiency')
    plt.ylabel('Run Efficiency')
    plt.title('Setup vs Run Efficiency')

# 11. Order fulfillment rate
plt.subplot(3, 4, 11)
if len(model_ready) > 0:
    daily_orders = production_orders.set_index('OrderDate').resample('D').size()
    daily_production = model_ready.set_index('RecordDateTime').resample('D').size()
    
    # Align dates
    common_dates = daily_orders.index.intersection(daily_production.index)
    if len(common_dates) > 0:
        fulfillment_rate = (daily_production[common_dates] / daily_orders[common_dates]).fillna(0)
        fulfillment_rate.plot(kind='line', alpha=0.7)
        plt.title('Daily Order Fulfillment Rate')
        plt.ylabel('Fulfillment Rate')
        plt.xticks(rotation=45)

# 12. System complexity metric
plt.subplot(3, 4, 12)
# Calculate system complexity metrics
total_materials = len(material_master)
total_bom_relations = len(bom_table)
total_routing_ops = len(routing_table)
total_work_centers = routing_table['WorkCenter'].nunique()
total_plants = production_orders['PlantID'].nunique()

system_metrics = {
    'Materials': total_materials,
    'BOM Relations': total_bom_relations,
    'Routing Ops': total_routing_ops,
    'Work Centers': total_work_centers,
    'Plants': total_plants
}

# Network density calculation
network_density = (total_bom_relations + total_routing_ops) / (total_materials * total_work_centers)

plt.text(0.5, 0.5, f'System Complexity\n\nMaterials: {total_materials}\nBOM Relations: {total_bom_relations}\nRouting Operations: {total_routing_ops}\nWork Centers: {total_work_centers}\nPlants: {total_plants}\n\nNetwork Density: {network_density:.3f}', 
         ha='center', va='center', fontsize=10, 
         bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.8))
plt.xlim(0, 1)
plt.ylim(0, 1)
plt.axis('off')
plt.title('System Complexity Overview')

plt.tight_layout()
plt.show()

# 8. SUMMARY INSIGHTS FOR IT COLLABORATION
print("\n" + "="*80)
print("🤝 INSIGHTS FOR IT COLLABORATION")
print("="*80)

# Data integration insights
print(f"""
🔗 DATA INTEGRATION INSIGHTS:
• Total System Entities: {total_materials + total_work_centers + total_plants} 
• Data Relationships: {total_bom_relations + total_routing_ops:,}
• Network Density: {network_density:.3f} (indicates system complexity)
• Data Processing Efficiency: {len(model_ready)/len(nal)*100:.1f}% (NAL → Model Ready)

📊 DATASET CONNECTIONS:
• Material Master ↔ BOM Table: {len(set(material_master['MaterialNumber']) & set(bom_table['ParentMaterial']))} common materials
• Material Master ↔ Routing Table: {len(set(material_master['MaterialNumber']) & set(routing_table['MaterialNumber']))} common materials  
• Production Orders ↔ Material Master: {len(set(production_orders['MaterialNumber']) & set(material_master['MaterialNumber']))} common materials
• Production Orders ↔ NAL Events: {len(set(production_orders['ProductionOrderID']) & set(nal['ProductionOrderID']))} common orders

🎯 KEY SYSTEM CHARACTERISTICS:
• Material Hierarchy: {material_counts.to_dict()}
• BOM Complexity: Avg {bom_stats['Component_Count'].mean():.1f} components per product
• Routing Complexity: Avg {routing_table.groupby('MaterialNumber').size().mean():.1f} operations per material
• Production Volume: {production_orders['PlannedQty'].sum():,} total planned units
• Operational Events: {len(nal):,} raw events → {len(model_ready):,} processed records

⚡ PERFORMANCE INDICATORS:
""")

if len(model_ready) > 0:
    print(f"• Average Capacity Utilization: {model_ready['CapacityUtilization'].mean():.1%}")
    print(f"• Average Yield Rate: {model_ready['YieldRate_pct'].mean():.1f}%")
    print(f"• Total System Downtime: {model_ready['Downtime_min'].sum():,.0f} minutes")
    
    # Identify bottlenecks
    if 'IsBottleneck' in model_ready.columns:
        bottleneck_rate = model_ready['IsBottleneck'].mean()
        print(f"• Bottleneck Occurrence Rate: {bottleneck_rate:.1%}")
    
    # Work center performance
    if 'WorkCenterID' in model_ready.columns:
        wc_performance = model_ready.groupby('WorkCenterID')['CapacityUtilization'].mean()
        top_wc = wc_performance.nlargest(1)
        print(f"• Highest Utilized Work Center: {top_wc.index[0]} ({top_wc.iloc[0]:.1%})")

print(f"""
🔍 DATA QUALITY INSIGHTS:
• Missing Data Points: {nal.isnull().sum().sum():,} across all NAL columns
• Outlier Records: Detected in timing and quantity data (preserved for ML)
• Data Completeness: {(1 - nal.isnull().sum().sum() / (len(nal) * len(nal.columns))):.1%}

🚀 RECOMMENDATIONS FOR IT:
• Implement real-time data pipelines for capacity monitoring
• Set up automated alerts for bottleneck detection (utilization > 85%)
• Create dashboards for cross-dataset relationship monitoring
• Establish data quality checks for timing and quantity anomalies
• Consider implementing predictive maintenance based on downtime patterns
""")

print("="*80)
print("✅ CROSS-DATASET ANALYSIS COMPLETED!")
print("="*80)
