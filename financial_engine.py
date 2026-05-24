
import pandas as pd
import numpy as np
import numpy_financial as npf
from datetime import datetime

def calculate_financials(user_inputs):
    initial_investment = user_inputs["initial_investment"]
    lifetime = user_inputs["lifetime"]
    salvage_value = user_inputs["salvage_value"]
    depr_method = user_inputs["depr_method"]
    tax_credit = user_inputs["tax_credit"]

    revenue_year1 = user_inputs["revenue_year1"]
    cogs_items = user_inputs["cogs_items"]
    opex_items = user_inputs["opex_items"]
    tax_rate = user_inputs["tax_rate"]

    discount_approach = user_inputs["discount_approach"]
    if discount_approach == 1:
        discount_rate = user_inputs["discount_rate"]
    else:
        beta = user_inputs["beta"]
        risk_free = user_inputs["risk_free"]
        market_premium = user_inputs["market_premium"]
        debt_ratio = user_inputs["debt_ratio"]
        cost_of_debt = user_inputs["cost_of_debt"]
        discount_rate = (1 - debt_ratio) * (risk_free + beta * market_premium) + debt_ratio * cost_of_debt

    initial_wc = user_inputs["initial_wc"]
    wc_percent = user_inputs["wc_percent"]
    wc_salvage = user_inputs["wc_salvage"]

    growth_revenue = user_inputs["growth_revenue"]
    growth_cogs = user_inputs["growth_cogs"]
    growth_opex = user_inputs["growth_opex"]

    years = list(range(1, lifetime + 1))
    df = pd.DataFrame(index=years)
    df.index.name = "Year"

    # --- Revenue ---
    df["Revenue"] = 0.0
    df.loc[1, "Revenue"] = revenue_year1
    for year in years[1:]:
        growth = next((rate for start, end, rate in growth_revenue if start <= year <= end), 0.0)
        df.loc[year, "Revenue"] = df.loc[year - 1, "Revenue"] * (1 + growth)

    # --- COGS ---
    df["- COGS"] = 0.0
    df.loc[1, "- COGS"] = sum(cogs_items.values())
    for year in years[1:]:
        growth = next((rate for start, end, rate in growth_cogs if start <= year <= end), 0.0)
        df.loc[year, "- COGS"] = df.loc[year - 1, "- COGS"] * (1 + growth)

    # --- Opex ---
    df["- Opex"] = 0.0
    df.loc[1, "- Opex"] = sum(opex_items.values())
    for year in years[1:]:
        growth = next((rate for start, end, rate in growth_opex if start <= year <= end), 0.0)
        df.loc[year, "- Opex"] = df.loc[year - 1, "- Opex"] * (1 + growth)

    # --- Depreciation ---
    if depr_method == 1:
        depreciation = [initial_investment / lifetime] * lifetime
    else:
        depreciation = []
        book = initial_investment
        for i in range(1, lifetime + 1):
            if i != lifetime:
                dep = book * 2 / lifetime
                depreciation.append(dep)
                book -= dep
            else:
                depreciation.append(book)
    df["- Depreciation"] = depreciation

    # --- Calculations ---
    df["Gross Profit"] = df["Revenue"] - df["- COGS"]
    df["EBITDA"] = df["Gross Profit"] - df["- Opex"]
    df["EBIT"] = df["EBITDA"] - df["- Depreciation"]
    df["- Tax"] = df["EBIT"].apply(lambda x: tax_rate * x if x > 0 else 0)
    df["EBIT(1-t)"] = df["EBIT"] - df["- Tax"]
    df["+ Deprec"] = df["- Depreciation"]

    # --- Working Capital Change ---
    wc_change = []
    wc_accum = initial_wc
    for year in years:
        wc_req = df.loc[year, "Revenue"] * wc_percent
        delta = wc_req - wc_accum
        wc_change.append(delta)
        wc_accum += delta
    df["- WC Change"] = wc_change

    # --- Net Cash Flow ---
    df["Net Cash"] = df["EBIT(1-t)"] + df["+ Deprec"] - df["- WC Change"]

    # --- Discount Factors ---
    df["Discount"] = [(1 / ((1 + discount_rate) ** i)) for i in years]

    # --- Final Discounted CF with Salvage Adjustments ---
    wc_total = initial_wc + sum(df["- WC Change"])
    terminal_value = salvage_value + wc_total * wc_salvage
    df["Discounted CF"] = df["Net Cash"] * df["Discount"]
    df.loc[lifetime, "Discounted CF"] += terminal_value * df.loc[lifetime, "Discount"]

    # --- NPV, IRR, ROC ---
    cashflows = [-initial_investment] + df["Net Cash"].tolist()
    cashflows[-1] += terminal_value
    npv = npf.npv(discount_rate, cashflows)
    irr = npf.irr(cashflows)
    roc = df["EBIT(1-t)"].sum() / initial_investment

    summary = pd.DataFrame({
        "Indicator": ["NPV", "IRR", "Return on Capital"],
        "Value": [npv, irr, roc]
    })

    # --- Reorder Columns ---
    desired_order = [
        "Revenue", "- COGS", "Gross Profit", "- Opex", "EBITDA",
        "- Depreciation", "EBIT", "- Tax", "EBIT(1-t)", "+ Deprec",
        "- WC Change", "Net Cash", "Discount", "Discounted CF"
    ]
    df = df[desired_order]
    df.index.name = "Year"

    # --- Export ---
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"financial_analysis_output_{timestamp}.xlsx"
    filepath = f"{filename}"
    with pd.ExcelWriter(filepath, engine="xlsxwriter") as writer:
        df.to_excel(writer, sheet_name="Operating Cashflows")
        summary.to_excel(writer, sheet_name="Summary", index=False)

    return filepath
