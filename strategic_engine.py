
# =========================================================
# Strategic Engine for Smart Business Advisor
# Purpose:
# 1) Generate SWOT Strategic Analysis
# 2) Generate Strategy Matrix: SO / ST / WO / WT
# 3) Support educational explanation for MBA-style strategic thinking
# =========================================================


def build_swot_context(plan_data):
    """
    Convert plan_data into a clear SWOT context string for GPT prompting.
    Expected keys:
    - business_info
    - strengths
    - weaknesses
    - opportunities
    - threats
    """

    return f"""
Business Info:
{plan_data.get("business_info", "")}

Strengths:
{plan_data.get("strengths", "")}

Weaknesses:
{plan_data.get("weaknesses", "")}

Opportunities:
{plan_data.get("opportunities", "")}

Threats:
{plan_data.get("threats", "")}
"""


def get_strategic_analysis_prompt(plan_data):
    """
    Prompt for SWOT Strategic Analysis.
    This stage should help students understand how SWOT items become strategic issues.
    """

    swot_context = build_swot_context(plan_data)

    return f"""
คุณคือที่ปรึกษาด้านการจัดทำแผนกลยุทธ์และแผนธุรกิจระดับ MBA

โปรดวิเคราะห์ SWOT Strategic Analysis จากข้อมูลต่อไปนี้:

{swot_context}

งานที่ต้องทำ:
1. วิเคราะห์ความหมายเชิงกลยุทธ์ของ SWOT ที่ผู้ใช้ยืนยันแล้ว
2. จับคู่ SWOT ที่มีนัยสำคัญเชิงยุทธศาสตร์ เช่น
   - Strengths + Opportunities
   - Strengths + Threats
   - Weaknesses + Opportunities
   - Weaknesses + Threats
3. อธิบายว่าแต่ละคู่มีความหมายเชิงกลยุทธ์อย่างไร
4. สรุป Strategic Issues สำคัญที่ควรนำไปใช้ในการกำหนด Vision, Mission, Objectives และ Strategy

รูปแบบคำตอบ:
ให้ตอบเป็นภาษาไทย โดยจัดเป็นหัวข้อดังนี้

# SWOT Strategic Analysis

## 1. ประเด็นเชิงกลยุทธ์จาก Strengths + Opportunities (SO)
- ระบุคู่ SWOT ที่มีนัยสำคัญ
- อธิบายความหมายเชิงกลยุทธ์

## 2. ประเด็นเชิงกลยุทธ์จาก Strengths + Threats (ST)
- ระบุคู่ SWOT ที่มีนัยสำคัญ
- อธิบายความหมายเชิงกลยุทธ์

## 3. ประเด็นเชิงกลยุทธ์จาก Weaknesses + Opportunities (WO)
- ระบุคู่ SWOT ที่มีนัยสำคัญ
- อธิบายความหมายเชิงกลยุทธ์

## 4. ประเด็นเชิงกลยุทธ์จาก Weaknesses + Threats (WT)
- ระบุคู่ SWOT ที่มีนัยสำคัญ
- อธิบายความหมายเชิงกลยุทธ์

## 5. Strategic Issues สำคัญที่ควรนำไปใช้ต่อ
เขียนเป็น numbered list 5-8 ข้อ

เงื่อนไขสำคัญ:
- อย่าสร้างข้อมูลใหม่ที่ไม่เกี่ยวข้องกับ SWOT
- ให้ใช้ข้อมูลที่ผู้ใช้ยืนยันแล้วเป็นฐาน
- อธิบายให้เหมาะกับการเรียนรู้ของนักศึกษา MBA
- ไม่ต้องเขียน Vision, Mission, Objectives หรือ Strategy ในขั้นตอนนี้
"""


def get_strategy_matrix_prompt(plan_data, strategic_analysis="", vision="", mission="", objectives=""):
    """
    Prompt for generating Strategy Matrix after Vision/Mission/Objectives.
    It explicitly connects strategies to SWOT pairings.
    """

    swot_context = build_swot_context(plan_data)

    return f"""
คุณคือที่ปรึกษาด้านกลยุทธ์ธุรกิจระดับ MBA

โปรดจัดทำ Strategy Matrix จาก SWOT ที่ผู้ใช้ยืนยันแล้ว โดยใช้ข้อมูลต่อไปนี้:

{swot_context}

SWOT Strategic Analysis:
{strategic_analysis}

Vision:
{vision}

Mission:
{mission}

Objectives:
{objectives}

งานที่ต้องทำ:
ให้สร้างกลยุทธ์จากการจับคู่ SWOT โดยแสดงให้เห็นว่าแต่ละกลยุทธ์มาจากตรรกะใด

รูปแบบคำตอบ:
ให้ตอบเป็นภาษาไทย และจัดเป็นหัวข้อดังนี้

# Strategy Matrix Based on SWOT Analysis

## 1. SO Strategies: กลยุทธ์เชิงรุก-รุก
หลักการ: ใช้จุดแข็งเพื่อฉกฉวยโอกาส
สำหรับแต่ละกลยุทธ์ให้แสดง:
- คู่ SWOT ที่ใช้ เช่น S1 + O2
- กลยุทธ์ที่เสนอ
- เหตุผลเชิงกลยุทธ์
- ผลลัพธ์ที่คาดหวัง

## 2. ST Strategies: กลยุทธ์ใช้จุดแข็งรับมือภัยคุกคาม
หลักการ: ใช้จุดแข็งเพื่อลดผลกระทบจากภัยคุกคาม
สำหรับแต่ละกลยุทธ์ให้แสดง:
- คู่ SWOT ที่ใช้ เช่น S2 + T1
- กลยุทธ์ที่เสนอ
- เหตุผลเชิงกลยุทธ์
- ผลลัพธ์ที่คาดหวัง

## 3. WO Strategies: กลยุทธ์ใช้โอกาสแก้จุดอ่อน
หลักการ: ใช้โอกาสภายนอกเพื่อแก้ไขหรือชดเชยจุดอ่อน
สำหรับแต่ละกลยุทธ์ให้แสดง:
- คู่ SWOT ที่ใช้ เช่น W1 + O3
- กลยุทธ์ที่เสนอ
- เหตุผลเชิงกลยุทธ์
- ผลลัพธ์ที่คาดหวัง

## 4. WT Strategies: กลยุทธ์ลด ละ เลิก หรือป้องกันความเสี่ยง
หลักการ: ลดจุดอ่อนและหลีกเลี่ยงภัยคุกคาม
สำหรับแต่ละกลยุทธ์ให้แสดง:
- คู่ SWOT ที่ใช้ เช่น W2 + T2
- สิ่งที่ควรลด / ละ / เลิก / หลีกเลี่ยง
- เหตุผลเชิงกลยุทธ์
- ผลลัพธ์ที่คาดหวัง

## 5. Recommended Priority Strategies
คัดเลือกกลยุทธ์ที่สำคัญที่สุด 3-5 กลยุทธ์ พร้อมเหตุผล

เงื่อนไขสำคัญ:
- ให้กลยุทธ์เชื่อมโยงกับ SWOT อย่างชัดเจน
- อย่าเสนอ strategy แบบลอย ๆ
- เน้นประโยชน์เชิงการศึกษาให้นักศึกษาเห็นตรรกะการวิเคราะห์
- ใช้ภาษาไทยที่ชัดเจน เป็นทางการพอสมควร แต่เข้าใจง่าย
"""


def process_strategic_analysis(client, model, plan_data):
    """
    Generate SWOT Strategic Analysis using OpenAI client.
    """

    prompt = get_strategic_analysis_prompt(plan_data)

    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
    )

    return response.choices[0].message.content.strip()


def process_strategy_matrix(
    client,
    model,
    plan_data,
    strategic_analysis="",
    vision="",
    mission="",
    objectives="",
):
    """
    Generate SO/ST/WO/WT strategy matrix.
    """

    prompt = get_strategy_matrix_prompt(
        plan_data=plan_data,
        strategic_analysis=strategic_analysis,
        vision=vision,
        mission=mission,
        objectives=objectives,
    )

    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
    )

    return response.choices[0].message.content.strip()
