import pandas as pd
from fpdf import FPDF
from datetime import timedelta
import matplotlib.pyplot as plt
import os

# -----------------------------
# PATH SETUP
# -----------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FONT_PATH = os.path.join(BASE_DIR, "..", "fonts", "DejaVuSans-Bold.ttf")
DATA_PATH = os.path.join(BASE_DIR, "..", "data", "Coffe_sales.csv")
REPORTS_DIR = os.path.join(BASE_DIR, "..", "reports")
CHARTS_DIR = os.path.join(REPORTS_DIR, "charts")

os.makedirs(REPORTS_DIR, exist_ok=True)
os.makedirs(CHARTS_DIR, exist_ok=True)

# -----------------------------
# LOAD DATA
# -----------------------------
df = pd.read_csv(DATA_PATH)
df["Date"] = pd.to_datetime(df["Date"])

# -----------------------------
# PDF CLASS
# -----------------------------
class CafeReportPDF(FPDF):
    def __init__(self, title):
        super().__init__()
        self.title = title
        self.set_auto_page_break(auto=True, margin=15)

        # ----- REGISTER FONTS -----
        self.add_font(
            "DejaVu", "", 
            r"C:/Users/GF63/cafe-automated-reporting-bot/fonts/DejaVuSans.ttf", 
            uni=True
        )
        self.add_font(
            "DejaVu", "B", 
            r"C:/Users/GF63/cafe-automated-reporting-bot/fonts/DejaVuSans-Bold.ttf", 
            uni=True
        )

        # ----- SET DEFAULT FONT -----
        self.set_font("DejaVu", "", size=12)


    def header(self):
        self.set_font("DejaVu", style="B", size=16)
        self.cell(0, 10, self.title, ln=True)
        self.ln(3)

    def footer(self):
        self.set_y(-15)
        self.set_font("DejaVu", size=8)
        self.cell(0, 10, "Generated automatically by Cafe Reporting Bot", align="C")

# -----------------------------
# UTILITY FUNCTIONS
# -----------------------------
def percentage_change(current, previous):
    if previous == 0:
        return 0
    return ((current - previous) / previous) * 100

def generate_revenue_chart(data, title, filename):
    if data.empty:
        return False

    daily_revenue = data.groupby("Date")["money"].sum()
    if daily_revenue.empty:
        return False

    plt.figure()
    daily_revenue.plot(marker="o")
    plt.title(title)
    plt.xlabel("Date")
    plt.ylabel("Revenue (RM)")
    plt.tight_layout()
    plt.savefig(filename)
    plt.close()
    return True

def generate_coffee_sales_chart(df, title, output_path):
    if df.empty or "coffee_name" not in df.columns:
        print("No coffee sales data available for chart.")
        return None

    sales = (
        df.groupby("coffee_name")
        .size()
        .sort_values(ascending=True)  # bottom → top for horizontal bar
    )

    if sales.empty:
        print("Coffee sales aggregation empty.")
        return None

    plt.figure(figsize=(8, max(4, len(sales) * 0.4)))
    plt.barh(sales.index, sales.values)
    plt.title(title)
    plt.xlabel("Cups Sold")
    plt.tight_layout()

    plt.savefig(output_path)
    plt.close()

    return output_path


# -----------------------------
# WEEKLY REPORT
# -----------------------------
def generate_weekly_report(df):
    latest_date = df["Date"].max()
    current_week_start = latest_date - timedelta(days=6)
    previous_week_start = current_week_start - timedelta(days=7)

    df_current = df[df["Date"] >= current_week_start]
    df_previous = df[(df["Date"] >= previous_week_start) & (df["Date"] < current_week_start)]

    print("\n=== WEEKLY DATA PREVIEW ===")
    print(df_current.head())
    print("Weekly rows:", len(df_current))

    if df_current.empty:
        print("No weekly data. Skipping report.")
        return

    current_revenue = df_current["money"].sum()
    previous_revenue = df_previous["money"].sum()
    change_pct = percentage_change(current_revenue, previous_revenue)
    trend = "INCREASE" if change_pct >= 0 else "DECREASE"

    pdf = CafeReportPDF("WEEKLY CAFE SALES REPORT")
    pdf.add_page()

    pdf.cell(0, 8, f"Week: {current_week_start.date()} to {latest_date.date()}", ln=True)
    pdf.cell(0, 8, f"Total Revenue: RM {current_revenue:.2f}", ln=True)
    pdf.cell(0, 8, f"Change vs Last Week: {trend} ({change_pct:.1f}%)", ln=True)
    pdf.ln(4)

    # --- Revenue Chart ---
    revenue_chart = os.path.join(CHARTS_DIR, "weekly_revenue.png")
    if generate_revenue_chart(df_current, "Daily Revenue (This Week)", revenue_chart):
        pdf.image(revenue_chart, w=180)
        pdf.ln(6)

    # --- Coffee Sales Chart ---
    coffee_chart = os.path.join(CHARTS_DIR, "weekly_coffee_sales.png")
    chart = generate_coffee_sales_chart(
        df_current,
        "Coffee Sales Breakdown (This Week)",
        coffee_chart
    )

    if chart and os.path.exists(chart):
        pdf.set_font("DejaVu", "B", 13)
        pdf.cell(0, 8, "Coffee Performance", ln=True)
        pdf.set_font("DejaVu", "", 12)
        pdf.image(chart, w=180)
        pdf.ln(6)

    # --- Peak Hour ---
    hourly_sales = df_current.groupby("hour_of_day")["money"].sum()
    peak_hour = hourly_sales.idxmax()
    peak_value = hourly_sales.max()

    pdf.set_font("DejaVu", "B", 13)
    pdf.cell(0, 8, "Peak Hour", ln=True)
    pdf.set_font("DejaVu", "", 12)
    pdf.cell(0, 8, f"{peak_hour}:00 - {peak_hour+1}:00 (RM {peak_value:.2f})", ln=True)

    # --- Insights ---
    pdf.ln(4)
    pdf.set_font("DejaVu", "B", 13)
    pdf.cell(0, 8, "Owner Actionable Insights", ln=True)
    pdf.set_font("DejaVu", "", 12)

    insights = (
        [
            "Sales declined compared to last week.",
            "Review low-performing drinks.",
            "Run promotions during off-peak hours."
        ] if change_pct < 0 else
        [
            "Sales increased compared to last week.",
            "Ensure stock for best-selling drinks.",
            "Upsell add-ons during peak hours."
        ]
    )

    for i in insights:
        pdf.cell(0, 8, f"- {i}", ln=True)

    output = os.path.join(REPORTS_DIR, "weekly_cafe_report.pdf")
    pdf.output(output)
    return output


# -----------------------------
# MONTHLY REPORT
# -----------------------------
def generate_monthly_report(df):
    latest_date = df["Date"].max()
    current_month = latest_date.to_period("M")
    previous_month = current_month - 1

    df_current = df[df["Date"].dt.to_period("M") == current_month]
    df_previous = df[df["Date"].dt.to_period("M") == previous_month]

    print("\n=== MONTHLY DATA PREVIEW ===")
    print(df_current.head())
    print("Monthly rows:", len(df_current))
    if df_current.empty:
        print("No monthly data. Skipping report.")
        return

    current_revenue = df_current["money"].sum()
    previous_revenue = df_previous["money"].sum()
    change_pct = percentage_change(current_revenue, previous_revenue)
    trend = "INCREASE" if change_pct >= 0 else "DECREASE"

    month_name = df_current["Date"].dt.strftime("%B %Y").iloc[0]
    chart_path = os.path.join(CHARTS_DIR, "monthly_revenue.png")
    generate_revenue_chart(df_current, f"Daily Revenue ({month_name})", chart_path)

    # --- PDF ---
    pdf = CafeReportPDF("MONTHLY CAFE SALES REPORT")
    pdf.add_page()
    pdf.cell(0, 8, f"Month: {month_name}", ln=True)
    pdf.cell(0, 8, f"Total Revenue: RM {current_revenue:.2f}", ln=True)
    pdf.cell(0, 8, f"Change vs Last Month: {trend} ({change_pct:.1f}%)", ln=True)
    pdf.ln(4)

    # --- Coffee Sales Chart ---
    coffee_chart = os.path.join(CHARTS_DIR, "monthly_coffee_sales.png")
    chart = generate_coffee_sales_chart(
        df_current,
        f"Coffee Sales Breakdown ({month_name})",
        coffee_chart
    )

    if chart and os.path.exists(chart):
        pdf.set_font("DejaVu", "B", 13)
        pdf.cell(0, 8, "Coffee Performance", ln=True)
        pdf.set_font("DejaVu", "", 12)
        pdf.image(chart, w=180)
        pdf.ln(6)


    # --- Best & Worst Selling Day ---
    daily_sales = df_current.groupby("Date")["money"].sum()
    best_day = daily_sales.idxmax()
    worst_day = daily_sales.idxmin()
    pdf.ln(4)
    pdf.set_font("DejaVu", style="B", size=13)
    pdf.cell(0, 8, "Best & Worst Selling Day", ln=True)
    pdf.set_font("DejaVu", size=12)
    pdf.cell(0, 8, f"Best Day: {best_day.date()} (RM {daily_sales.max():.2f})", ln=True)
    pdf.cell(0, 8, f"Worst Day: {worst_day.date()} (RM {daily_sales.min():.2f})", ln=True)
    
    
    if os.path.exists(chart_path):
        pdf.image(chart_path, w=180)
        pdf.ln(6)

    # --- Actionable Insights ---
    pdf.ln(4)
    pdf.set_font("DejaVu", style="B", size=13)
    pdf.cell(0, 8, "Monthly Owner Strategy", ln=True)
    pdf.set_font("DejaVu", size=12)
    insights = (
        [
            "Monthly sales declined.",
            "Launch loyalty campaigns.",
            "Bundle slow-moving items.",
            "Improve weekday traffic."
        ]
        if change_pct < 0 else
        [
            "Strong monthly growth.",
            "Scale inventory.",
            "Test premium pricing.",
            "Prepare staffing for growth."
        ]
    )
    for i in insights:
        pdf.cell(0, 8, f"- {i}", ln=True)

    output = os.path.join(REPORTS_DIR, "monthly_cafe_report.pdf")
    pdf.output(output)
    return output

# -----------------------------
# RUN REPORTS
# -----------------------------
print("Weekly report generated:", generate_weekly_report(df))
print("Monthly report generated:", generate_monthly_report(df))
