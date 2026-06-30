# workflow_utils.py

def normalize_text(text):
    return str(text).strip().lower()


def is_requesting_suggestion(text):
    t = normalize_text(text)
    keywords = [
        "ช่วยคิด", "ช่วยแนะนำ", "แนะนำ", "ยกตัวอย่าง",
        "ช่วยเสนอ", "คิดให้", "เสนอให้", "ขอคำแนะนำ",
        "แนะนำเพิ่ม", "แนะนำเพิ่มเติม", "ช่วยดู",
        "suggest", "example", "recommend",
    ]
    return any(k in t for k in keywords)


def is_revision_intent(text):
    t = normalize_text(text)

    revision_keywords = [
        "แก้", "แก้ไข", "ปรับ", "ปรับปรุง", "เปลี่ยน",
        "ลบ", "ตัด", "เอาออก", "เพิ่มเติม", "เพิ่ม",
        "แทรก", "ย้าย", "รวมข้อ", "แยกข้อ",
        "ให้สั้นลง", "ให้กระชับ", "ให้ชัดเจน",
        "edit", "revise", "delete", "remove", "add", "insert",
    ]

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