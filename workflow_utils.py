# workflow_utils.py
import re

def normalize_text(text):
    return str(text).strip().lower()


def is_requesting_suggestion(text):
    t = normalize_text(text)

    suggestion_phrases = [
        "ขอคำแนะนำ",
        "ขอคำแนะนำเพิ่มเติม",
        "ช่วยแนะนำ",
        "ช่วยแนะนำเพิ่มเติม",
        "แนะนำเพิ่มเติม",
        "แนะนำเพิ่ม",
        "ช่วยเสนอ",
        "ช่วยเสนอเพิ่มเติม",
        "ช่วยคิด",
        "ช่วยคิดเพิ่มเติม",
        "ยกตัวอย่าง",
        "ขอตัวอย่าง",
        "suggest",
        "recommend",
        "example",
    ]

    return any(p in t for p in suggestion_phrases)


def is_revision_intent(text):
    t = normalize_text(text)

    # ถ้าเป็นการขอคำแนะนำจาก AI ไม่ให้ถือว่าเป็นคำสั่งแก้ไข
    if is_requesting_suggestion(t):
        return False

    revision_keywords = [
        "แก้",
        "แก้ไข",
        "ปรับ",
        "ปรับปรุง",
        "เปลี่ยน",
        "ลบ",
        "ตัด",
        "เอาออก",
        "เพิ่มเติม",
        "เพิ่ม",
        "แทรก",
        "ย้าย",
        "รวมข้อ",
        "แยกข้อ",
        "ให้สั้นลง",
        "ให้กระชับ",
        "ให้ชัดเจน",
        "edit",
        "revise",
        "delete",
        "remove",
        "add",
        "insert",
    ]

    if re.search(r"ข้อ\s*\d+", t):
        return True

    return any(k in t for k in revision_keywords)


def is_empty_revision_request(text):
    t = normalize_text(text)
    words = [
        "แก้", "แก้ไข", "เพิ่มเติม", "แก้ไขเพิ่มเติม",
        "ลบ", "ปรับปรุง", "edit", "revise",
    ]
    return t in words


def is_go_next(text):
    t = normalize_text(text)

    if is_requesting_suggestion(t):
        return False

    if is_revision_intent(t):
        return False

    next_patterns = [
        "ต่อไป", "ขั้นต่อไป", "ทำต่อ", "ทำต่อไป", "ทำขั้นต่อไป",
        "ช่วยทำต่อ", "ช่วยทำต่อไป", "ช่วยทำขั้นต่อไป",
        "ไปต่อ", "ไปขั้นต่อไป", "ดำเนินการต่อ", "ดำเนินขั้นต่อไป",
        "next", "continue",
    ]

    confirm_patterns = [
        "ไม่แก้", "ไม่แก้ไข", "พอแล้ว", "เสร็จแล้ว",
        "ยืนยัน", "ใช้ได้", "ตามนี้", "โอเค", "ok",
    ]

    return (
        any(p in t for p in next_patterns)
        or any(t == p or t.startswith(p) for p in confirm_patterns)
    )