import yfinance as yf
import pandas as pd
import sqlite3
import matplotlib.pyplot as plt

# ==========================================
# 1. הגדרות בסיס ופרמטרים
# ==========================================
tickers = ['SPLG', 'VOO', 'IVV']
# דמי ניהול שנתיים (נכון ל-2025/26)
expense_ratios = {'SPLG': 0.0002, 'VOO': 0.0003, 'IVV': 0.0003}

initial_investment = 100000  # סכום השקעה התחלתי בש"ח
avg_annual_return = 0.10     # תשואה שנתית ממוצעת משוערת (10%)
projection_years = 30        # טווח זמן לסימולציה

# ==========================================
# 2. הורדת נתונים היסטוריים (ETL)
# ==========================================
print("--- שואב נתונים היסטוריים מ-Yahoo Finance ---")
# מושכים מ-2010 (השנה שבה VOO הושקה) כדי שיהיה בסיס השוואה רחב ב-SQL
raw_data = yf.download(tickers, start="2010-09-07")

# טיפול חסין בתקלות במבנה העמודות של Pandas
if 'Adj Close' in raw_data.columns:
    data = raw_data['Adj Close']
else:
    data = raw_data['Close']

data = data.dropna()

# ==========================================
# 3. אחסון בבסיס נתונים (SQL Storage)
# ==========================================
conn = sqlite3.connect('long_term_investing.db')
# הפיכת האינדקס (תאריך) לעמודה רגילה ושמירה בטבלה
data.reset_index().to_sql('historical_prices', conn, if_exists='replace', index=False)
print(f"--- נתוני אמת נשמרו בטבלת SQL. סה\"כ שורות: {len(data)} ---")

# ==========================================
# 4. סימולציית ריבית דריבית ל-30 שנה
# ==========================================
future_years = list(range(0, projection_years + 1))
plt.figure(figsize=(12, 8))

# הגדרת סגנונות קו שונים כדי שנוכל לראות את כל הקרנות בנפרד
styles = {'SPLG': '-', 'VOO': '--', 'IVV': ':'}
colors = {'SPLG': '#1f77b4', 'VOO': '#ff7f0e', 'IVV': '#2ca02c'}

print(f"\n--- תחזית ל-{projection_years} שנה (השקעה של {initial_investment:,} ש\"ח) ---")

final_results = {}

for ticker, fee in expense_ratios.items():
    # חישוב הערך העתידי בכל שנה: A = P * (1 + r - f)^t
    yearly_values = [initial_investment * ((1 + avg_annual_return - fee) ** t) for t in future_years]
    plt.plot(future_years, yearly_values,
             label=f"{ticker} (Fee: {fee * 100:.2f}%)",
             linestyle=styles[ticker],
             color=colors[ticker],
             linewidth=2.5)

    final_results[ticker] = yearly_values[-1]
    print(f"{ticker}: סכום סופי: {yearly_values[-1]:,.0f} ש\"ח")

no_fee_values = [initial_investment * ((1 + avg_annual_return) ** t) for t in future_years]
plt.plot(future_years, no_fee_values, label='S&P 500 Index (0% Fee)',
         linestyle='-.', color='black', alpha=0.4)

# ==========================================
plt.title(f'The Power of Compound Interest: {projection_years}-Year Projection', fontsize=16, pad=20)
plt.xlabel('Years from Today', fontsize=12)
plt.ylabel('Portfolio Value (ILS)', fontsize=12)
plt.grid(True, which='both', linestyle='--', alpha=0.5)
plt.legend(loc='upper left', fontsize=11)

gap = final_results['SPLG'] - final_results['VOO']
plt.annotate(f'Fee Savings (SPLG vs VOO):\n{gap:,.0f} ILS',
             xy=(projection_years, final_results['SPLG']),
             xytext=(projection_years-8, final_results['SPLG'] * 0.8),
             arrowprops=dict(facecolor='black', shrink=0.05, width=1),
             fontsize=11, fontweight='bold', color='#1f77b4')

plt.ticklabel_format(style='plain', axis='y')
plt.tight_layout()

print("\n--- מציג את הגרף הסופי. הפרויקט הושלם בהצלחה! ---")
plt.savefig('investment_graph.png')

plt.show()

conn.close()