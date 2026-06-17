import pandas as pd
import numpy as np
import numpy_financial as npf
from datetime import datetime


def _get_growth_rate(growth_list, year):
    if not growth_list:
        return 0.0
    for start, end, rate in growth_list:
        if start <= year <= end:
            return float(rate)
    return 0.0


def _calculate_depreciation(initial_investment, salvage_value, lifetime, depr_method):
    initial_investment = float(initial_investment)
    salvage_value = float(salvage_value)
    lifetime = int(lifetime)
    depreciable_base = max(initial_investment - salvage_value, 0)

    if lifetime <= 0:
        raise ValueError("Project lifetime must be greater than zero.")

    if depr_method == 1:
        return [depreciable_base / lifetime] * lifetime

    depreciation = []
    book_value = initial_investment
    for year in range(1, lifetime + 1):
        if book_value <= salvage_value:
            dep = 0.0
        else:
            ddb_dep = book_value * (2 / lifetime)
            max_allowed_dep = book_value - salvage_value
            dep = min(ddb_dep, max_allowed_dep)
        depreciation.append(dep)
        book_value -= dep
    return depreciation


def _make_year0_display_row(df, total_initial_outlay):
    """
    Add Year 0 to the Excel output table.
    Year 0 shows only the cash-flow stream used for NPV/IRR:
    Net Cash, Discount, and Discounted CF.
    """
    df_export = df.copy()
    year0 = pd.DataFrame(index=[0], columns=df_export.columns)
    year0.index.name = "Year"
    year0.loc[0, :] = np.nan
    year0.loc[0, "Net Cash"] = -total_initial_outlay
    year0.loc[0, "Discount"] = 1.0
    year0.loc[0, "Discounted CF"] = -total_initial_outlay
    df_export = pd.concat([year0, df_export], axis=0)
    df_export.index.name = "Year"
    return df_export


def calculate_financials(user_inputs):
    # =========================================================
    # 1. Read Inputs
    # =========================================================
    initial_investment = float(user_inputs["initial_investment"])
    lifetime = int(user_inputs["lifetime"])
    salvage_value = float(user_inputs.get("salvage_value", 0))
    depr_method = int(user_inputs.get("depr_method", 1))
    tax_credit = float(user_inputs.get("tax_credit", 0))

    revenue_year1 = float(user_inputs["revenue_year1"])
    cogs_items = user_inputs.get("cogs_items", {})
    opex_items = user_inputs.get("opex_items", {})
    tax_rate = float(user_inputs.get("tax_rate", 0))

    discount_approach = int(user_inputs.get("discount_approach", 1))
    if discount_approach == 1:
        discount_rate = float(user_inputs["discount_rate"])
    else:
        beta = float(user_inputs.get("beta", 0))
        risk_free = float(user_inputs.get("risk_free", 0))
        market_premium = float(user_inputs.get("market_premium", 0))
        debt_ratio = float(user_inputs.get("debt_ratio", 0))
        cost_of_debt = float(user_inputs.get("cost_of_debt", 0))
        cost_of_equity = risk_free + beta * market_premium
        discount_rate = (1 - debt_ratio) * cost_of_equity + debt_ratio * cost_of_debt

    initial_wc = float(user_inputs.get("initial_wc", 0))
    wc_percent = float(user_inputs.get("wc_percent", 0))
    wc_salvage = float(user_inputs.get("wc_salvage", 1))

    growth_revenue = user_inputs.get("growth_revenue", [])
    growth_cogs = user_inputs.get("growth_cogs", [])
    growth_opex = user_inputs.get("growth_opex", [])

    # =========================================================
    # 2. Initial Outlay, time 0
    # =========================================================
    tax_credit_amount = initial_investment * tax_credit
    net_fixed_investment = initial_investment - tax_credit_amount
    total_initial_outlay = net_fixed_investment + initial_wc

    # =========================================================
    # 3. Projection Table, years 1 to N
    # =========================================================
    years = list(range(1, lifetime + 1))
    df = pd.DataFrame(index=years)
    df.index.name = "Year"

    df["Revenue"] = 0.0
    df.loc[1, "Revenue"] = revenue_year1
    for year in years[1:]:
        growth = _get_growth_rate(growth_revenue, year)
        df.loc[year, "Revenue"] = df.loc[year - 1, "Revenue"] * (1 + growth)

    df["- COGS"] = 0.0
    df.loc[1, "- COGS"] = sum(float(v) for v in cogs_items.values())
    for year in years[1:]:
        growth = _get_growth_rate(growth_cogs, year)
        df.loc[year, "- COGS"] = df.loc[year - 1, "- COGS"] * (1 + growth)

    df["- Opex"] = 0.0
    df.loc[1, "- Opex"] = sum(float(v) for v in opex_items.values())
    for year in years[1:]:
        growth = _get_growth_rate(growth_opex, year)
        df.loc[year, "- Opex"] = df.loc[year - 1, "- Opex"] * (1 + growth)

    df["- Depreciation"] = _calculate_depreciation(
        initial_investment=initial_investment,
        salvage_value=salvage_value,
        lifetime=lifetime,
        depr_method=depr_method,
    )

    df["Gross Profit"] = df["Revenue"] - df["- COGS"]
    df["EBITDA"] = df["Gross Profit"] - df["- Opex"]
    df["EBIT"] = df["EBITDA"] - df["- Depreciation"]
    df["- Tax"] = df["EBIT"].apply(lambda x: tax_rate * x if x > 0 else 0)
    df["EBIT(1-t)"] = df["EBIT"] - df["- Tax"]
    df["+ Deprec"] = df["- Depreciation"]

    wc_change = []
    accumulated_wc = initial_wc
    for year in years:
        required_wc = df.loc[year, "Revenue"] * wc_percent
        delta_wc = required_wc - accumulated_wc
        wc_change.append(delta_wc)
        accumulated_wc += delta_wc

    df["Required WC"] = df["Revenue"] * wc_percent
    df["- WC Change"] = wc_change

    df["Net Cash"] = df["EBIT(1-t)"] + df["+ Deprec"] - df["- WC Change"]

    final_required_wc = df.loc[lifetime, "Required WC"]
    terminal_value = salvage_value + (final_required_wc * wc_salvage)
    df["Terminal Value"] = 0.0
    df.loc[lifetime, "Terminal Value"] = terminal_value

    df["Discount"] = [1 / ((1 + discount_rate) ** year) for year in years]
    df["Discounted CF"] = (df["Net Cash"] + df["Terminal Value"]) * df["Discount"]

    cashflows = [-total_initial_outlay] + (df["Net Cash"] + df["Terminal Value"]).tolist()
    npv = npf.npv(discount_rate, cashflows)
    irr = npf.irr(cashflows)
    roc = df["EBIT(1-t)"].sum() / total_initial_outlay if total_initial_outlay != 0 else np.nan

    summary = pd.DataFrame({
        "Indicator": [
            "Initial Investment",
            "Tax Credit Amount",
            "Net Fixed Investment",
            "Initial Working Capital",
            "Total Initial Outlay",
            "Discount Rate",
            "Terminal Value",
            "NPV",
            "IRR",
            "Return on Capital",
        ],
        "Value": [
            initial_investment,
            tax_credit_amount,
            net_fixed_investment,
            initial_wc,
            total_initial_outlay,
            discount_rate,
            terminal_value,
            npv,
            irr,
            roc,
        ],
    })

    desired_order = [
        "Revenue",
        "- COGS",
        "Gross Profit",
        "- Opex",
        "EBITDA",
        "- Depreciation",
        "EBIT",
        "- Tax",
        "EBIT(1-t)",
        "+ Deprec",
        "Required WC",
        "- WC Change",
        "Net Cash",
        "Terminal Value",
        "Discount",
        "Discounted CF",
    ]
    df = df[desired_order]

    # This is the table written to Excel. It includes Year 0.
    df_export = _make_year0_display_row(df, total_initial_outlay)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"financial_analysis_output_{timestamp}.xlsx"

    with pd.ExcelWriter(filename, engine="xlsxwriter") as writer:
        df_export.to_excel(writer, sheet_name="Operating Cashflows")
        summary.to_excel(writer, sheet_name="Summary", index=False)

        workbook = writer.book
        money_format = workbook.add_format({"num_format": "#,##0.00"})
        percent_format = workbook.add_format({"num_format": "0.00%"})
        header_format = workbook.add_format({"bold": True, "bg_color": "#D9EAD3", "border": 1})

        ws1 = writer.sheets["Operating Cashflows"]
        ws2 = writer.sheets["Summary"]

        ws1.set_column(0, 0, 10)
        ws1.set_column(1, len(df_export.columns), 18, money_format)
        ws2.set_column(0, 0, 28)
        ws2.set_column(1, 1, 18, money_format)

        for col_num, value in enumerate(df_export.reset_index().columns):
            ws1.write(0, col_num, value, header_format)

        for col_num, value in enumerate(summary.columns):
            ws2.write(0, col_num, value, header_format)

        for row_num, indicator in enumerate(summary["Indicator"], start=1):
            if indicator in ["Discount Rate", "IRR", "Return on Capital"]:
                ws2.write(row_num, 1, summary.loc[row_num - 1, "Value"], percent_format)

    return filename
