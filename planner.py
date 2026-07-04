
def get_swot_prompt():
    return """You're a business advisor guiding a user through a SWOT Analysis.
Ask the user to describe:

1. **Strengths**  
Questions to consider:
- What internal advantages give your business an edge?
- Do you have skilled staff, loyal customers, or strong brand recognition?

2. **Weaknesses**  
Questions to consider:
- What internal limitations hold your business back?
- Do you lack experience, resources, or face quality/service issues?

3. **Opportunities**  
Questions to consider:
- What external trends or needs can you take advantage of?
- Are there new markets, technologies, or unmet needs?

4. **Threats**  
Questions to consider:
- What external risks could challenge your business?
- Are there economic shifts, competitors, or legal risks?

After each input, acknowledge and ask for the next point.
When all four are complete, summarize in a table.
Please enter Strengths in the box ✏️ Type your message below, then press Send"""

def get_vision_prompt():
    return """Based on the SWOT, help the user define:
- Vision (long-term aspiration)
- Mission (core purpose)
- SMART Objectives (3–5 goals that are Specific, Measurable, Achievable, Relevant, Time-bound)
- Use realistic deadlines that reflect the current date, e.g., 6–12 months from now."""

def get_strategy_prompt():
    return """Based on SWOT and SMART Objectives, suggest 3–5 business strategies:
- Use strengths to capitalize on opportunities
- Mitigate weaknesses and avoid threats
- Align with goals and values"""

def get_marketing_step_prompt(step):
    steps = {
        1: """Step 1: Target Market

Who is your ideal customer?
Questions to consider:
- What age/income/location group?
- What are their core needs?Please enter your Target Market in the box ✏️ Type your message below, then press Send
""",

        2: """Step 2: Positioning Statement

What makes your business offering unique?
Questions to consider:
- How is it different from others?
- What value or benefit matters most to the customer?
Please enter your Market Positioning in the box ✏️ Type your message below, then press Send""",

        3: """Step 3: Marketing Objectives

Set 2–3 measurable goals.
Examples:
- Increase brand awareness by 30% in 6 months
- Acquire 50 qualified leads per month
Please enter your Marketing Objectives in the box ✏️ Type your message below, then press Send""",

        4: """Step 4: Marketing Mix (4Ps)

Provide details for:
- Product: Key features, services, benefits
- Price: Pricing strategy (premium, value, discount)
- Place: How/where customers access the service
- Promotion: Channels used (social media, events, ads)
Please enter your Marketing Mix in the box ✏️ Type your message below, then press Send""",

        5: """Step 5: Marketing Summary

Summarize your full marketing plan using inputs from Steps 1–4."""
    }
    return steps.get(step, "Unknown step. Please restart the marketing plan.")

def get_marketing_summary_prompt(user_inputs):
    prompt = """
You're a marketing strategist. Write a clear, professional, and insight-rich marketing plan summary based on the user's provided inputs.
Analyze each component, synthesize key insights, and highlight strengths or gaps if any.
Present it in a structured and polished tone like a professional business document.

Here are the inputs:
"""
    prompt += f"\n1. Target Market: {user_inputs.get('step1', '[Not Provided]')}"
    prompt += f"\n2. Positioning Statement: {user_inputs.get('step2', '[Not Provided]')}"
    prompt += f"\n3. Marketing Objectives: {user_inputs.get('step3', '[Not Provided]')}"
    prompt += f"\n4. Marketing Mix (4Ps): {user_inputs.get('step4', '[Not Provided]')}"
    prompt += "\n\nNow generate a final summary paragraph that reflects a strategic marketing vision."
    return prompt

def get_executive_summary_prompt(language, user_inputs):
    business_info = user_inputs.get("business_info", "[Not Provided]")
    swot = user_inputs.get("swot_summary", "[Not Provided]")
    vision = user_inputs.get("vision_mission", "[Not Provided]")
    strategy = user_inputs.get("strategy", "[Not Provided]")
    marketing = user_inputs.get("marketing", "[Not Provided]")

    if language == "th":
        return f"""
คุณคือผู้เชี่ยวชาญด้านกลยุทธ์ธุรกิจ
กรุณาสรุปแผนธุรกิจจากข้อมูลต่อไปนี้เป็นภาษาไทยในรูปแบบที่มืออาชีพ กระชับ ชัดเจน ใช้ภาษาทางธุรกิจ

- ข้อมูลธุรกิจ: {business_info}
- SWOT: {swot}
- วิสัยทัศน์ พันธกิจ เป้าหมาย: {vision}
- กลยุทธ์: {strategy}
- แผนการตลาด: {marketing}

เขียน Executive Summary ที่ครอบคลุมจุดเด่น โอกาส และแนวทางโดยรวมของแผนธุรกิจนี้
"""
    else:
        return f"""
You're a business strategy consultant.
Summarize the following business plan inputs into a concise, polished Executive Summary:

- Business Info: {business_info}
- SWOT: {swot}
- Vision, Mission, Objectives: {vision}
- Strategies: {strategy}
- Marketing Plan: {marketing}

Use a confident, strategic tone. Focus on insights, strategic alignment, and value proposition.
"""

# ✅ NEW FUNCTION FOR FINANCIAL INPUTS
def get_financial_step_prompt(step):
    prompts = {
        1: """📊 Step 1: INITIAL INVESTMENT

Please enter the following (separated by commas):
1. Initial Investment Amount
2. Lifetime of the investment (number of years)
3. Salvage Value
4. Depreciation Method (1 = Straight-Line, 2 = DDB)
5. Tax Credit (as a decimal, e.g., 0.1 for 10%)""",

        2: """💵 Step 2: CASHFLOW DETAILS

Please enter the following values separated by commas:
1. Revenue in Year 1
2. COGS - Materials
3. COGS - Direct Labor
4. Opex - Rent
5. Opex - Salaries
6. Opex - Marketing
7. Opex - Office Supplies
8. Opex - Utilities
9. Tax Rate on Net Income (e.g., 0.4 for 40%)""",

        3: """📉 Step 3: DISCOUNT RATE

Enter either direct rate or CAPM parameters.
- If using Direct Approach (enter: 1, rate)
- If using CAPM/WACC (enter: 2, beta, risk-free rate, market premium, debt ratio, cost of debt)

Example (direct): 1, 0.1  
Example (CAPM): 2, 0.9, 0.08, 0.055, 0.3, 0.09""",

        4: """💼 Step 4: WORKING CAPITAL

Please enter the following (comma-separated):
1. Initial Working Capital
2. % of Revenue allocated to Working Capital (e.g., 0.25 = 25%)
3. % of Working Capital recovered at the end (e.g., 1.0 = 100%)""",

        5: """📈 Step 5: GROWTH RATES

Provide up to 4 growth ranges each for Revenue, COGS, and Operating Expenses.

Input format for each is:
FromYear.ToYear.GrowthRate;...  
Example for Revenue: 1.5.0.05; 6.8.0.03; 9.10.0.02

Please enter the 3 rows (Revenue, COGS, Opex) **separated by line breaks** in the box below and press Send.
"""
    }
    return prompts.get(step, "❌ Unknown financial step.")