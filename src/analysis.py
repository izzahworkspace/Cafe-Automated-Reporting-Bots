import pandas as pd

# Load café sales data
df = pd.read_csv("C:/Users/GF63/cafe-automated-reporting-bot/data/Coffe_sales.csv")

# Basic cleaning
df["money"] = pd.to_numeric(df["money"], errors="coerce")
df = df.dropna(subset=["money"])

# Core metrics
total_revenue = df["money"].sum()
total_orders = len(df)
top_coffee = df["coffee_name"].value_counts().idxmax()
peak_hour = df["hour_of_day"].value_counts().idxmax()
busiest_day = df["Weekday"].value_counts().idxmax()

# Automated report output
print("☕ Café Automated Sales Report")
print("--------------------------------")
print(f"Total Revenue: RM {total_revenue:.2f}")
print(f"Total Orders: {total_orders}")
print(f"Top-Selling Coffee: {top_coffee}")
print(f"Peak Hour: {peak_hour}:00")
print(f"Busiest Day: {busiest_day}")
