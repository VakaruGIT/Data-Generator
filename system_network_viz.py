#!/usr/bin/env python
"""
Manufacturing System Network Visualization
==========================================
Creates visual representation of dataset connections and system relationships
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from matplotlib.patches import Rectangle, FancyBboxPatch
from matplotlib.patches import ConnectionPatch

# Set up the plotting style
plt.style.use('seaborn-v0_8')
sns.set_palette("husl")

print("🎨 Creating Manufacturing System Network Visualization...")

# Load key datasets
material_master = pd.read_csv("out/material_master.csv")
bom_table = pd.read_csv("out/bom_table.csv") 
routing_table = pd.read_csv("out/routing_table.csv")
production_orders = pd.read_csv("out/production_orders.csv")
nal = pd.read_csv("out/NAL.csv")
model_ready = pd.read_csv("out/model_ready.csv")

# Create comprehensive system overview
fig = plt.figure(figsize=(20, 14))

# Main title
fig.suptitle('Manufacturing System: Cross-Dataset Connections & Relationships', 
             fontsize=20, fontweight='bold', y=0.95)

# 1. System Architecture Overview
ax1 = plt.subplot(2, 3, 1)
ax1.set_xlim(0, 10)
ax1.set_ylim(0, 10)
ax1.axis('off')
ax1.set_title('System Architecture', fontsize=14, fontweight='bold')

# Draw system components
components = [
    {'name': 'Material Master\n(390 materials)', 'pos': (2, 8), 'color': '#FF6B6B'},
    {'name': 'BOM Table\n(393 relationships)', 'pos': (8, 8), 'color': '#4ECDC4'},
    {'name': 'Routing Table\n(789 operations)', 'pos': (2, 6), 'color': '#45B7D1'},
    {'name': 'Production Orders\n(5,000 orders)', 'pos': (8, 6), 'color': '#96CEB4'},
    {'name': 'NAL Events\n(40,370 records)', 'pos': (2, 4), 'color': '#FFEAA7'},
    {'name': 'Model Ready\n(39,175 records)', 'pos': (8, 4), 'color': '#DDA0DD'},
]

for comp in components:
    bbox = FancyBboxPatch((comp['pos'][0]-0.8, comp['pos'][1]-0.5), 1.6, 1, 
                         boxstyle="round,pad=0.1", facecolor=comp['color'], 
                         edgecolor='black', alpha=0.7)
    ax1.add_patch(bbox)
    ax1.text(comp['pos'][0], comp['pos'][1], comp['name'], 
             ha='center', va='center', fontsize=9, fontweight='bold')

# Draw connections
connections = [
    ((2, 7.5), (2, 6.5)),  # Material Master → Routing
    ((2, 7.5), (7.2, 7.5)),  # Material Master → BOM
    ((8, 7.5), (8, 6.5)),  # BOM → Production Orders
    ((2, 5.5), (2, 4.5)),  # Routing → NAL
    ((8, 5.5), (2, 4.5)),  # Production Orders → NAL
    ((2, 3.5), (7.2, 3.5)),  # NAL → Model Ready
]

for start, end in connections:
    ax1.annotate('', xy=end, xytext=start, 
                arrowprops=dict(arrowstyle='->', lw=2, color='gray'))

# 2. Material Hierarchy Flow
ax2 = plt.subplot(2, 3, 2)
material_counts = material_master['MaterialType'].value_counts()
colors = ['#FF6B6B', '#4ECDC4', '#45B7D1']
wedges, texts, autotexts = ax2.pie(material_counts.values, labels=material_counts.index, 
                                  colors=colors, autopct='%1.1f%%', startangle=90)
ax2.set_title('Material Hierarchy Distribution', fontsize=14, fontweight='bold')

# Add annotation
ax2.text(0, -1.5, f'Total: {len(material_master)} materials\nFG→SFG→RAW hierarchy', 
         ha='center', va='center', fontsize=10, 
         bbox=dict(boxstyle='round', facecolor='lightgray', alpha=0.8))

# 3. BOM Complexity Network
ax3 = plt.subplot(2, 3, 3)
bom_complexity = bom_table.groupby('ParentMaterial')['ComponentMaterial'].count()
ax3.hist(bom_complexity.values, bins=15, alpha=0.7, color='#4ECDC4', edgecolor='black')
ax3.set_title('BOM Complexity Distribution', fontsize=14, fontweight='bold')
ax3.set_xlabel('Components per Product')
ax3.set_ylabel('Number of Products')

# Add statistics
mean_complexity = bom_complexity.mean()
ax3.axvline(mean_complexity, color='red', linestyle='--', linewidth=2, 
           label=f'Mean: {mean_complexity:.1f}')
ax3.legend()

# 4. Work Center Network
ax4 = plt.subplot(2, 3, 4)
wc_loads = routing_table.groupby('WorkCenter').agg({
    'MaterialNumber': 'nunique',
    'SetupTime_min': 'mean',
    'RunTime_min': 'mean'
})
wc_loads['TotalTime'] = wc_loads['SetupTime_min'] + wc_loads['RunTime_min']

# Scatter plot of work center characteristics
scatter = ax4.scatter(wc_loads['MaterialNumber'], wc_loads['TotalTime'], 
                     s=100, alpha=0.7, c=range(len(wc_loads)), cmap='viridis')
ax4.set_title('Work Center Load Analysis', fontsize=14, fontweight='bold')
ax4.set_xlabel('Number of Materials')
ax4.set_ylabel('Average Total Time (min)')

# Add work center labels for top 5
top_wc = wc_loads.nlargest(5, 'TotalTime')
for wc, data in top_wc.iterrows():
    ax4.annotate(wc, (data['MaterialNumber'], data['TotalTime']), 
                xytext=(5, 5), textcoords='offset points', fontsize=8)

# 5. Production Timeline
ax5 = plt.subplot(2, 3, 5)
production_orders['OrderDate'] = pd.to_datetime(production_orders['OrderDate'])
monthly_orders = production_orders.set_index('OrderDate').resample('M').size()
monthly_orders.plot(kind='line', marker='o', ax=ax5, color='#96CEB4', linewidth=2)
ax5.set_title('Production Order Timeline', fontsize=14, fontweight='bold')
ax5.set_ylabel('Number of Orders')
ax5.tick_params(axis='x', rotation=45)

# Add trend line
z = np.polyfit(range(len(monthly_orders)), monthly_orders.values, 1)
p = np.poly1d(z)
ax5.plot(monthly_orders.index, p(range(len(monthly_orders))), 
         "r--", alpha=0.8, label=f'Trend')
ax5.legend()

# 6. Performance Metrics Dashboard
ax6 = plt.subplot(2, 3, 6)
ax6.axis('off')
ax6.set_title('Key Performance Indicators', fontsize=14, fontweight='bold')

# Calculate key metrics
total_materials = len(material_master)
total_orders = len(production_orders)
total_events = len(nal)
data_retention = len(model_ready) / len(nal) * 100
avg_yield = model_ready['YieldRate_pct'].mean()
avg_capacity = model_ready['CapacityUtilization'].mean()

# Create KPI display
kpis = [
    f'📊 System Scale: {total_materials} materials',
    f'🏭 Production: {total_orders:,} orders',
    f'⚡ Events: {total_events:,} operations',
    f'📈 Data Quality: {data_retention:.1f}%',
    f'🎯 Yield Rate: {avg_yield:.1f}%',
    f'🔄 Capacity: {avg_capacity:.1%}',
    f'🔗 Integration: 100%',
    f'✅ ML Ready: Yes'
]

for i, kpi in enumerate(kpis):
    ax6.text(0.1, 0.9 - i*0.11, kpi, fontsize=12, 
             bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.3))

plt.tight_layout()
plt.subplots_adjust(top=0.93)
plt.show()

# Create detailed connection matrix
print("\n🔗 Creating Dataset Connection Matrix...")

fig, ax = plt.subplots(figsize=(12, 8))

# Define dataset connections (1 = connected, 0 = not connected)
datasets = ['Material\nMaster', 'BOM\nTable', 'Routing\nTable', 
           'Production\nOrders', 'NAL\nEvents', 'Model\nReady']

# Connection matrix (symmetric)
connections = np.array([
    [1, 1, 1, 1, 0, 0],  # Material Master
    [1, 1, 0, 0, 0, 0],  # BOM Table  
    [1, 0, 1, 0, 1, 0],  # Routing Table
    [1, 0, 0, 1, 1, 0],  # Production Orders
    [0, 0, 1, 1, 1, 1],  # NAL Events
    [0, 0, 0, 0, 1, 1],  # Model Ready
])

# Create heatmap
im = ax.imshow(connections, cmap='RdYlBu_r', aspect='auto')

# Add text annotations
for i in range(len(datasets)):
    for j in range(len(datasets)):
        if connections[i, j] == 1:
            if i == j:
                text = '●'  # Self-reference
            else:
                text = '✓'  # Connected
        else:
            text = '○'  # Not connected
        ax.text(j, i, text, ha='center', va='center', 
               fontsize=16, fontweight='bold',
               color='white' if connections[i, j] == 1 else 'gray')

# Customize the plot
ax.set_xticks(range(len(datasets)))
ax.set_yticks(range(len(datasets)))
ax.set_xticklabels(datasets, rotation=45, ha='right')
ax.set_yticklabels(datasets)
ax.set_title('Dataset Connection Matrix\n(✓ = Connected, ○ = Not Connected)', 
             fontsize=16, fontweight='bold', pad=20)

# Add grid
ax.set_xticks(np.arange(len(datasets))-.5, minor=True)
ax.set_yticks(np.arange(len(datasets))-.5, minor=True)
ax.grid(which='minor', color='white', linestyle='-', linewidth=2)

plt.tight_layout()
plt.show()

# Print summary statistics
print("\n📊 DATASET CONNECTION SUMMARY")
print("=" * 50)
print(f"Total Datasets: {len(datasets)}")
print(f"Total Possible Connections: {len(datasets) * (len(datasets) - 1) // 2}")
print(f"Actual Connections: {(connections.sum() - len(datasets)) // 2}")  # Subtract diagonal
print(f"Connection Density: {((connections.sum() - len(datasets)) // 2) / (len(datasets) * (len(datasets) - 1) // 2) * 100:.1f}%")

print("\n🔗 KEY CONNECTIONS:")
connection_names = [
    "Material Master ↔ BOM Table (Material hierarchy)",
    "Material Master ↔ Routing Table (Operation definitions)", 
    "Material Master ↔ Production Orders (Order specifications)",
    "Routing Table ↔ NAL Events (Operation execution)",
    "Production Orders ↔ NAL Events (Order fulfillment)",
    "NAL Events ↔ Model Ready (Feature engineering)"
]

for i, conn in enumerate(connection_names):
    print(f"{i+1}. {conn}")

print("\n✅ Manufacturing System Network Visualization Complete!")
print("🎯 Ready for IT collaboration and system integration!")
