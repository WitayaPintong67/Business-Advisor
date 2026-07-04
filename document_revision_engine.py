# document_revision_engine.py

import re


def parse_revision_instruction(text):
    t = text.lower().strip()

    result = {
        "action": "unknown",
        "item_no": None,
        "old_text": None,
        "new_text": None,
        "insert_text": None
    }

    # -------------------------
    # Replace item
    # -------------------------
    m = re.search(r"ข้อ\s*(\d+).*เป็น\s*(.+)", t)

    if m:
        result["action"] = "replace_item"
        result["item_no"] = int(m.group(1))
        result["new_text"] = m.group(2).strip()
        return result

    # -------------------------
    # Delete item
    # -------------------------
    m = re.search(r"ลบข้อ\s*(\d+)", t)

    if m:
        result["action"] = "delete_item"
        result["item_no"] = int(m.group(1))
        return result

    # -------------------------
    # Delete specific text
    # -------------------------
    m = re.search(
        r"ข้อ\s*(\d+).*?(ลบ|ตัด).*?ข้อความ.*?(?:ออก)?\s*(.+)",
        t
    )

    if m:
        result["action"] = "delete_text"
        result["item_no"] = int(m.group(1))
        result["old_text"] = m.group(3).strip()
        return result

    # -------------------------
    # Insert after text
    # -------------------------
    if "เติม" in t or "เพิ่ม" in t or "แทรก" in t:
        result["action"] = "insert"
        return result

    return result

def revise_document_with_gpt(
    client,
    model,
    document_label,
    current_draft,
    user_instruction,
    business_context="",
):
    
    parsed_instruction = parse_revision_instruction(
    user_instruction
)   
    prompt = f"""
คุณคือผู้ช่วยแก้ไขเอกสารอย่างแม่นยำ

บริบทของธุรกิจ:
{business_context}

เอกสารที่กำลังแก้ไข:
{document_label}

ฉบับปัจจุบัน:
{current_draft}

คำสั่งแก้ไขจากผู้ใช้:
{user_instruction}

คำสั่งที่ระบบตีความได้:
{parsed_instruction}

กติกาสำคัญมาก:
- ต้องแก้จากฉบับปัจจุบันเท่านั้น
- ถ้าผู้ใช้สั่งว่า "แก้ข้อ X เป็น ..." หรือ "ปรับข้อ X เป็น ..." ให้ใช้ข้อความหลังคำว่า "เป็น" แทนข้อ X โดยตรงให้มากที่สุด
- ถ้าผู้ใช้สั่ง "ตัดข้อความ..." หรือ "ลบข้อความ..." ให้ลบข้อความนั้นออกจากข้อที่ระบุ
- ห้ามเติมคำใหม่ที่ผู้ใช้ไม่ได้ระบุ เช่น "เราตั้งเป้าที่จะ" เว้นแต่จำเป็นจริง ๆ
- แก้เฉพาะส่วนที่ผู้ใช้สั่งแก้
- คงข้ออื่นที่ผู้ใช้ไม่ได้สั่งแก้ไว้
- ถ้าผู้ใช้สั่งเพิ่ม ให้เพิ่มเข้าไปในตำแหน่งที่เหมาะสม
- ถ้าผู้ใช้สั่งแทรก ให้แทรกตามตำแหน่งที่ระบุ
- ถ้าผู้ใช้สั่งลบ ให้ลบเฉพาะข้อหรือข้อความที่ระบุ
- หลังแก้ไขแล้ว ให้เรียงเลขรายการใหม่ให้ถูกต้อง
- ห้ามตอบเฉพาะข้อที่แก้ ต้องตอบเอกสารฉบับปรับปรุงแล้วทั้งหมด

รูปแบบคำตอบ:
- ตอบเป็นภาษาไทย
- แสดงเฉพาะเอกสารฉบับปรับปรุงแล้วเท่านั้น
- ไม่ต้องอธิบายกระบวนการคิด
"""

    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
    )

    return response.choices[0].message.content.strip()