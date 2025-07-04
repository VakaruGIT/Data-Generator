# Check if model_ready.csv that is in out folder 

import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv("out/model_ready.csv")

# Check if column RecordDateTime spans over 1 year 
if df['RecordDateTime'].dtype == 'object':
    df['RecordDateTime'] = pd.to_datetime(df['RecordDateTime'])
if df['RecordDateTime'].max() - df['RecordDateTime'].min() > pd.Timedelta(days=365):
    print("RecordDateTime spans over 1 year")
else:
    print("RecordDateTime does not span over 1 year")

# Check how many values per day 
df['Date'] = df['RecordDateTime'].dt.date
daily_counts = df['Date'].value_counts().sort_index()
print("Daily counts of records:")
print(daily_counts)

# Check how many values per hour
df['Hour'] = df['RecordDateTime'].dt.hour
hourly_counts = df['Hour'].value_counts().sort_index()
print("Hourly counts of records:")
print(hourly_counts)

# Check how many days per month the record span
df['Month'] = df['RecordDateTime'].dt.to_period('M')
monthly_counts = df['Month'].value_counts().sort_index()
print("Monthly counts of records:")
print(monthly_counts)


# Plot to see all the variables
import seaborn as sns
import numpy as np
from matplotlib.dates import DateFormatter

# Set style for better looking plots
plt.style.use('seaborn-v0_8')
sns.set_palette("husl")

# Create a figure with multiple subplots
fig = plt.figure(figsize=(20, 16))

# 1. Time Series Plot - Production activity over time
plt.subplot(3, 4, 1)
df_time = df.groupby('Date').size().reset_index(name='RecordCount')
df_time['Date'] = pd.to_datetime(df_time['Date'])
plt.plot(df_time['Date'], df_time['RecordCount'], alpha=0.7, linewidth=1)
plt.title('Production Activity Over Time')
plt.xlabel('Date')
plt.ylabel('Number of Records')
plt.xticks(rotation=45)

# 2. Hourly Distribution
plt.subplot(3, 4, 2)
plt.bar(hourly_counts.index, hourly_counts.values, alpha=0.7)
plt.title('Production by Hour of Day')
plt.xlabel('Hour')
plt.ylabel('Number of Records')

# 3. Monthly Distribution
plt.subplot(3, 4, 3)
monthly_counts.plot(kind='bar', alpha=0.7)
plt.title('Production by Month')
plt.xlabel('Month')
plt.ylabel('Number of Records')
plt.xticks(rotation=45)

# 4. Yield Rate Distribution
plt.subplot(3, 4, 4)
plt.hist(df['YieldRate_pct'], bins=30, alpha=0.7, edgecolor='black')
plt.title('Yield Rate Distribution')
plt.xlabel('Yield Rate (%)')
plt.ylabel('Frequency')

# 5. Downtime Analysis
plt.subplot(3, 4, 5)
downtime_by_reason = df.groupby('DowntimeReason')['Downtime_min'].sum().sort_values(ascending=False)
plt.bar(downtime_by_reason.index, downtime_by_reason.values, alpha=0.7)
plt.title('Downtime by Reason')
plt.xlabel('Downtime Reason')
plt.ylabel('Total Downtime (minutes)')
plt.xticks(rotation=45)

# 6. Setup Time vs Run Time Scatter
plt.subplot(3, 4, 6)
plt.scatter(df['SetupTime_Actual_min'], df['RunTime_Actual_min'], alpha=0.5, s=30)
plt.title('Setup Time vs Run Time')
plt.xlabel('Setup Time (minutes)')
plt.ylabel('Run Time (minutes)')

# 7. Product Complexity Distribution
plt.subplot(3, 4, 7)
complexity_cols = ['ProductComplexity_LOW', 'ProductComplexity_MED']
complexity_data = []
for col in complexity_cols:
    complexity_data.append(df[col].sum())
complexity_data.append(len(df) - sum(complexity_data))  # HIGH complexity
complexity_labels = ['LOW', 'MED', 'HIGH']
plt.pie(complexity_data, labels=complexity_labels, autopct='%1.1f%%', startangle=90)
plt.title('Product Complexity Distribution')

# 8. Machine Class Distribution
plt.subplot(3, 4, 8)
machine_cols = [col for col in df.columns if col.startswith('MachineClass_')]
machine_data = [df[col].sum() for col in machine_cols]
machine_labels = [col.replace('MachineClass_', '') for col in machine_cols]
# Add CNC (assuming it's the remaining)
machine_data.append(len(df) - sum(machine_data))
machine_labels.append('CNC')
plt.pie(machine_data, labels=machine_labels, autopct='%1.1f%%', startangle=90)
plt.title('Machine Class Distribution')

# 9. Planned vs Actual Quantity
plt.subplot(3, 4, 9)
plt.scatter(df['LotSize_Planned'], df['LotSize_Actual'], alpha=0.5, s=30)
plt.plot([df['LotSize_Planned'].min(), df['LotSize_Planned'].max()], 
         [df['LotSize_Planned'].min(), df['LotSize_Planned'].max()], 
         'r--', alpha=0.8)
plt.title('Planned vs Actual Lot Size')
plt.xlabel('Planned Lot Size')
plt.ylabel('Actual Lot Size')

# 10. Scrap Quantity Distribution
plt.subplot(3, 4, 10)
scrap_counts = df['ScrapQty'].value_counts().sort_index()
plt.bar(scrap_counts.index, scrap_counts.values, alpha=0.7)
plt.title('Scrap Quantity Distribution')
plt.xlabel('Scrap Quantity')
plt.ylabel('Frequency')

# 11. Plant Performance Comparison
plt.subplot(3, 4, 11)
plant_cols = [col for col in df.columns if col.startswith('PlantID_')]
plant_data = [df[col].sum() for col in plant_cols]
plant_labels = [col.replace('PlantID_', '') for col in plant_cols]
# Add PLT1 (assuming it's the remaining)
plant_data.append(len(df) - sum(plant_data))
plant_labels.append('PLT1')
plt.bar(plant_labels, plant_data, alpha=0.7)
plt.title('Production by Plant')
plt.xlabel('Plant ID')
plt.ylabel('Number of Records')

# 12. Weekday Pattern
plt.subplot(3, 4, 12)
weekday_counts = df['Weekday'].value_counts().sort_index()
weekday_labels = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
plt.bar(weekday_counts.index, weekday_counts.values, alpha=0.7)
plt.title('Production by Weekday')
plt.xlabel('Weekday')
plt.ylabel('Number of Records')
plt.xticks(range(7), weekday_labels)

plt.tight_layout()
plt.show()

# Additional detailed plots
print("\n" + "="*50)
print("ADDITIONAL ANALYSIS PLOTS")
print("="*50)

# Heatmap of production by hour and weekday
plt.figure(figsize=(12, 8))
heatmap_data = df.pivot_table(values='RecordDateTime', index='Weekday', columns='Hour', aggfunc='count', fill_value=0)
sns.heatmap(heatmap_data, annot=True, fmt='d', cmap='YlOrRd', cbar_kws={'label': 'Number of Records'})
plt.title('Production Heatmap: Hour vs Weekday')
plt.xlabel('Hour of Day')
plt.ylabel('Weekday')
plt.show()

# Performance metrics correlation
plt.figure(figsize=(15, 10))
performance_cols = ['SetupTime_Actual_min', 'RunTime_Actual_min', 'YieldRate_pct', 
                   'Downtime_min', 'ScrapQty', 'LotSize_Planned', 'LotSize_Actual']
corr_matrix = df[performance_cols].corr()
sns.heatmap(corr_matrix, annot=True, cmap='coolwarm', center=0, 
            square=True, linewidths=0.5, cbar_kws={'label': 'Correlation Coefficient'})
plt.title('Performance Metrics Correlation Matrix')
plt.show()

# Time series of key metrics
fig, axes = plt.subplots(2, 2, figsize=(15, 10))
df_daily = df.groupby('Date').agg({
    'YieldRate_pct': 'mean',
    'Downtime_min': 'sum',
    'ScrapQty': 'sum',
    'SetupTime_Actual_min': 'mean'
}).reset_index()
df_daily['Date'] = pd.to_datetime(df_daily['Date'])

# Plot 1: Daily Average Yield Rate
axes[0, 0].plot(df_daily['Date'], df_daily['YieldRate_pct'], alpha=0.7)
axes[0, 0].set_title('Daily Average Yield Rate')
axes[0, 0].set_ylabel('Yield Rate (%)')
axes[0, 0].tick_params(axis='x', rotation=45)

# Plot 2: Daily Total Downtime
axes[0, 1].plot(df_daily['Date'], df_daily['Downtime_min'], alpha=0.7, color='red')
axes[0, 1].set_title('Daily Total Downtime')
axes[0, 1].set_ylabel('Downtime (minutes)')
axes[0, 1].tick_params(axis='x', rotation=45)

# Plot 3: Daily Total Scrap
axes[1, 0].plot(df_daily['Date'], df_daily['ScrapQty'], alpha=0.7, color='orange')
axes[1, 0].set_title('Daily Total Scrap Quantity')
axes[1, 0].set_ylabel('Scrap Quantity')
axes[1, 0].tick_params(axis='x', rotation=45)

# Plot 4: Daily Average Setup Time
axes[1, 1].plot(df_daily['Date'], df_daily['SetupTime_Actual_min'], alpha=0.7, color='green')
axes[1, 1].set_title('Daily Average Setup Time')
axes[1, 1].set_ylabel('Setup Time (minutes)')
axes[1, 1].tick_params(axis='x', rotation=45)

plt.tight_layout()
plt.show()

# Box plots for performance by categories
fig, axes = plt.subplots(2, 2, figsize=(15, 10))

# Yield Rate by Product Complexity
complexity_data = []
if df['ProductComplexity_LOW'].sum() > 0:
    complexity_data.append(df[df['ProductComplexity_LOW'] == True]['YieldRate_pct'].values)
if df['ProductComplexity_MED'].sum() > 0:
    complexity_data.append(df[df['ProductComplexity_MED'] == True]['YieldRate_pct'].values)
# HIGH complexity (neither LOW nor MED)
high_complexity = df[(df['ProductComplexity_LOW'] == False) & (df['ProductComplexity_MED'] == False)]
if len(high_complexity) > 0:
    complexity_data.append(high_complexity['YieldRate_pct'].values)

axes[0, 0].boxplot(complexity_data, labels=['LOW', 'MED', 'HIGH'][:len(complexity_data)])
axes[0, 0].set_title('Yield Rate by Product Complexity')
axes[0, 0].set_ylabel('Yield Rate (%)')

# Downtime by Reason
downtime_reasons = df['DowntimeReason'].dropna().unique()
downtime_data = [df[df['DowntimeReason'] == reason]['Downtime_min'].values for reason in downtime_reasons]
axes[0, 1].boxplot(downtime_data, labels=downtime_reasons)
axes[0, 1].set_title('Downtime Distribution by Reason')
axes[0, 1].set_ylabel('Downtime (minutes)')
axes[0, 1].tick_params(axis='x', rotation=45)

# Setup Time by Machine Class
machine_classes = []
machine_data = []
for col in df.columns:
    if col.startswith('MachineClass_') and df[col].sum() > 0:
        machine_name = col.replace('MachineClass_', '')
        machine_classes.append(machine_name)
        machine_data.append(df[df[col] == True]['SetupTime_Actual_min'].values)

axes[1, 0].boxplot(machine_data, labels=machine_classes)
axes[1, 0].set_title('Setup Time by Machine Class')
axes[1, 0].set_ylabel('Setup Time (minutes)')
axes[1, 0].tick_params(axis='x', rotation=45)

# Scrap Quantity by Plant
plant_classes = []
plant_data = []
for col in df.columns:
    if col.startswith('PlantID_') and df[col].sum() > 0:
        plant_name = col.replace('PlantID_', '')
        plant_classes.append(plant_name)
        plant_data.append(df[df[col] == True]['ScrapQty'].values)

axes[1, 1].boxplot(plant_data, labels=plant_classes)
axes[1, 1].set_title('Scrap Quantity by Plant')
axes[1, 1].set_ylabel('Scrap Quantity')

plt.tight_layout()
plt.show()

print("\n" + "="*50)
print("SUMMARY STATISTICS")
print("="*50)
print(f"Total Records: {len(df):,}")
print(f"Date Range: {df['RecordDateTime'].min()} to {df['RecordDateTime'].max()}")
print(f"Average Yield Rate: {df['YieldRate_pct'].mean():.2f}%")
print(f"Total Downtime: {df['Downtime_min'].sum():,} minutes")
print(f"Average Setup Time: {df['SetupTime_Actual_min'].mean():.2f} minutes")
print(f"Average Run Time: {df['RunTime_Actual_min'].mean():.2f} minutes")
print(f"Total Scrap: {df['ScrapQty'].sum():,} units")




