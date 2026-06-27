# marketing_engine.py
# =========================================================
# Marketing Engine for Smart Business Advisor
# =========================================================

MARKETING_ITEMS = {
    "target_market": {
        "label_th": "ตลาดเป้าหมายและการแบ่งส่วนตลาด",
        "label_en": "Target Market & Segmentation",
        "next": "customer_persona",
        "description": "ระบุกลุ่มลูกค้าเป้าหมายหลัก การแบ่งส่วนตลาด และเหตุผลที่เลือกตลาดนั้น",
    },
    "customer_persona": {
        "label_th": "ลักษณะลูกค้าเป้าหมาย",
        "label_en": "Customer Persona",
        "next": "positioning",
        "description": "อธิบายลูกค้าเป้าหมายในเชิงพฤติกรรม ความต้องการ ปัญหา และแรงจูงใจ",
    },
    "positioning": {
        "label_th": "การวางตำแหน่งทางการตลาด",
        "label_en": "Positioning",
        "next": "marketing_mix",
        "description": "กำหนดว่าธุรกิจต้องการให้ลูกค้ารับรู้แบรนด์ สินค้า หรือบริการอย่างไรเมื่อเทียบกับคู่แข่ง",
    },
    "marketing_mix": {
        "label_th": "ส่วนประสมทางการตลาด",
        "label_en": "Marketing Mix",
        "next": "sales_channels",
        "description": "กำหนด Product, Price, Place, Promotion หรือ 7Ps หากเป็นธุรกิจบริการ",
    },
    "sales_channels": {
        "label_th": "ช่องทางการขายและการจัดจำหน่าย",
        "label_en": "Sales Channels",
        "next": "promotion_plan",
        "description": "ระบุช่องทางการเข้าถึงลูกค้า การขาย การให้บริการ และการกระจายสินค้า/บริการ",
    },
    "promotion_plan": {
        "label_th": "แผนการส่งเสริมการตลาด",
        "label_en": "Promotion Plan",
        "next": "marketing_kpi",
        "description": "กำหนดกิจกรรมสื่อสารการตลาด โปรโมชั่น แคมเปญ และการสร้างความสัมพันธ์กับลูกค้า",
    },
    "marketing_kpi": {
        "label_th": "ตัวชี้วัดทางการตลาด",
        "label_en": "Marketing KPIs",
        "next": None,
        "description": "กำหนดตัวชี้วัดเพื่อประเมินผลการตลาด เช่น จำนวนลูกค้า รายได้ อัตราการซื้อซ้ำ และ conversion rate",
    },
}


def normalize_text(text):
    return text.strip().lower()


def is_requesting_suggestion(text):
    t = normalize_text(text)
    keywords = [
        "ช่วยคิด", "ช่วยแนะนำ", "แนะนำ", "เสนอ", "ขอคำแนะนำ",
        "ตัวอย่าง", "คิดให้", "ช่วยเสนอ", "suggest", "recommend", "example",
    ]
    return any(k in t for k in keywords)


def is_go_next(text):
    t = normalize_text(text)

    negative_patterns = [
        "แนะนำ", "ขอคำแนะนำ", "ช่วยแนะนำ", "suggest",
        "recommend", "example", "ตัวอย่าง",
    ]
    if any(p in t for p in negative_patterns):
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


def is_empty_revision_request(text):
    t = normalize_text(text)
    words = ["แก้", "แก้ไข", "เพิ่มเติม", "แก้ไขเพิ่มเติม", "ลบ", "ปรับปรุง", "edit", "revise"]
    return t in words


def build_marketing_context(plan_data, strategic_analysis="", vision_mission_objectives=None, strategy_matrix=""):
    if vision_mission_objectives is None:
        vision_mission_objectives = {}

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

SWOT Strategic Analysis:
{strategic_analysis}

Vision:
{vision_mission_objectives.get("vision", "")}

Mission:
{vision_mission_objectives.get("mission", "")}

Objectives:
{vision_mission_objectives.get("objectives", "")}

Strategy Matrix:
{strategy_matrix}
"""


def get_marketing_intro_prompt(item_key):
    item = MARKETING_ITEMS[item_key]
    return (
        f"ขั้นตอนต่อไปคือการจัดทำ **{item['label_th']} ({item['label_en']})**\n\n"
        f"{item['description']}\n\n"
        f"คุณสามารถพิมพ์ {item['label_th']} ที่คุณคิดไว้เองได้เลยครับ\n\n"
        f"หรือถ้าต้องการให้ Chatbot ช่วยเสนอ {item['label_th']} จาก Business Info, SWOT, Strategy Matrix และ Objectives "
        f"ให้พิมพ์ว่า **ช่วยแนะนำ{item['label_th']}ให้หน่อย** ได้เลยครับ"
    )


def get_marketing_review_menu(item_key):
    item = MARKETING_ITEMS[item_key]
    return (
        f"\n\nโปรดตรวจสอบ **{item['label_th']} ({item['label_en']})** ข้างต้นครับ\n\n"
        "จากนั้นคุณสามารถเลือกทำอย่างใดอย่างหนึ่งต่อไปนี้:\n\n"
        "1. พิมพ์คำสั่ง **แก้ไข/เพิ่มเติม/ลบ/แทรก** เช่น\n"
        "   - ลบข้อ 3\n"
        "   - แก้ข้อ 2 ให้เน้นลูกค้ากลุ่มครอบครัวผู้สูงอายุ\n"
        "   - เพิ่มช่องทาง TikTok และ LINE OA\n"
        "   - แทรกข้อใหม่ระหว่างข้อ 2 และข้อ 3\n\n"
        "2. พิมพ์ว่า **ขอคำแนะนำ** ถ้าต้องการให้ Chatbot ช่วยเสนอประเด็นเพิ่มเติม โดยคงของเดิมไว้ให้มากที่สุด\n\n"
        "3. พิมพ์ว่า **ทำขั้นต่อไป** หรือ **ต่อไป** ถ้าพอใจแล้วและต้องการไปหัวข้อถัดไป"
    )


def _marketing_task(item_key):
    if item_key == "target_market":
        return """
โปรดเสนอ Target Market & Segmentation โดยระบุ:
1. กลุ่มตลาดหลัก
2. กลุ่มตลาดรอง
3. การแบ่งส่วนตลาด เช่น อายุ รายได้ พื้นที่ พฤติกรรม ความต้องการ
4. เหตุผลที่เลือกตลาดเป้าหมายนี้
"""
    if item_key == "customer_persona":
        return """
โปรดสร้าง Customer Persona 2-3 กลุ่ม โดยระบุ:
1. ชื่อ persona สมมติ
2. อายุ/สถานะ/บทบาท
3. ปัญหาและความต้องการ
4. พฤติกรรมการตัดสินใจซื้อ
5. สิ่งที่ธุรกิจควรสื่อสารกับลูกค้ากลุ่มนี้
"""
    if item_key == "positioning":
        return """
โปรดเสนอ Positioning โดยระบุ:
1. Positioning statement
2. จุดแตกต่างจากคู่แข่ง
3. คุณค่าหลักที่ต้องการให้ลูกค้ารับรู้
4. เหตุผลที่ positioning นี้สอดคล้องกับ SWOT และ Strategy Matrix
"""
    if item_key == "marketing_mix":
        return """
โปรดเสนอ Marketing Mix โดยเลือกใช้ 4Ps หรือ 7Ps ตามลักษณะธุรกิจ
ถ้าเป็นธุรกิจบริการ ควรใช้ 7Ps:
1. Product / Service
2. Price
3. Place
4. Promotion
5. People
6. Process
7. Physical Evidence
"""
    if item_key == "sales_channels":
        return """
โปรดเสนอ Sales Channels และ Distribution Plan โดยระบุ:
1. ช่องทาง offline
2. ช่องทาง online
3. ช่องทาง partner / referral
4. เหตุผลที่ช่องทางเหล่านี้เหมาะกับลูกค้าเป้าหมาย
"""
    if item_key == "promotion_plan":
        return """
โปรดเสนอ Promotion Plan โดยระบุ:
1. กิจกรรมส่งเสริมการตลาดระยะเริ่มต้น
2. กิจกรรมสร้างการรับรู้
3. กิจกรรมสร้างความน่าเชื่อถือ
4. กิจกรรมกระตุ้นการตัดสินใจซื้อ
5. แผนรักษาลูกค้าเดิม
"""
    return """
โปรดเสนอ Marketing KPIs โดยระบุ:
1. KPI ด้านการรับรู้แบรนด์
2. KPI ด้านลูกค้าเป้าหมาย
3. KPI ด้านยอดขายหรือรายได้
4. KPI ด้าน retention / repeat purchase
5. KPI ด้าน digital marketing ถ้าเกี่ยวข้อง
"""


def get_initial_marketing_prompt(item_key, plan_data, strategic_analysis="", vision_mission_objectives=None, strategy_matrix=""):
    item = MARKETING_ITEMS[item_key]
    context = build_marketing_context(plan_data, strategic_analysis, vision_mission_objectives, strategy_matrix)
    task = _marketing_task(item_key)

    return f"""
คุณคือที่ปรึกษาการตลาดและแผนธุรกิจระดับ MBA

ข้อมูลพื้นฐาน:
{context}

ขณะนี้ต้องการจัดทำ {item['label_th']} ({item['label_en']})

งานของคุณ:
{task}

เงื่อนไข:
- ตอบเป็นภาษาไทย
- ให้สอดคล้องกับ Business Info, SWOT, SWOT Strategic Analysis, Vision, Mission, Objectives และ Strategy Matrix
- อย่าเสนอสิ่งที่ขัดกับกลยุทธ์หลักของธุรกิจ
- เขียนให้เหมาะกับการนำไปใช้ใน Business Plan
- แสดงเฉพาะเนื้อหา {item['label_th']} ที่เสนอเท่านั้น
"""


def get_enhance_marketing_prompt(item_key, current_draft, plan_data, strategic_analysis="", vision_mission_objectives=None, strategy_matrix=""):
    item = MARKETING_ITEMS[item_key]
    context = build_marketing_context(plan_data, strategic_analysis, vision_mission_objectives, strategy_matrix)

    return f"""
คุณคือที่ปรึกษาการตลาดและผู้ช่วยทบทวนแผนธุรกิจ

ข้อมูลพื้นฐาน:
{context}

ขณะนี้ผู้ใช้กำลังทบทวน {item['label_th']} ({item['label_en']})

{item['label_th']} ฉบับปัจจุบัน:
{current_draft}

งานของคุณ:
1. คงสาระเดิมของผู้ใช้ไว้ให้มากที่สุด
2. ช่วยเพิ่มประเด็นที่สำคัญแต่ยังขาดอยู่
3. ถ้ามีข้อซ้ำ ให้รวมให้กระชับได้
4. ทำให้เนื้อหาสอดคล้องกับ Strategy Matrix และ Objectives มากขึ้น
5. อย่าเปลี่ยนความหมายหลักของข้อความเดิมโดยไม่จำเป็น

รูปแบบคำตอบ:
- ตอบเป็นภาษาไทย
- เขียนเป็นรายการหรือหัวข้อที่อ่านง่าย
- แสดงเฉพาะ {item['label_th']} ฉบับปรับปรุงแล้วเท่านั้น
- ไม่ต้องอธิบายกระบวนการคิด
"""


def get_revise_marketing_prompt(item_key, current_draft, user_instruction, plan_data, strategic_analysis="", vision_mission_objectives=None, strategy_matrix=""):
    item = MARKETING_ITEMS[item_key]
    context = build_marketing_context(plan_data, strategic_analysis, vision_mission_objectives, strategy_matrix)

    return f"""
คุณคือผู้ช่วยแก้ไขข้อความ Marketing Plan อย่างแม่นยำ

ข้อมูลพื้นฐาน:
{context}

ขณะนี้ผู้ใช้กำลังแก้ไข {item['label_th']} ({item['label_en']})

{item['label_th']} ฉบับปัจจุบัน:
{current_draft}

คำสั่งแก้ไขจากผู้ใช้:
{user_instruction}

กติกาสำคัญมาก:
- ถ้าผู้ใช้ระบุว่า "แก้ข้อ X เป็น ..." หรือ "ปรับข้อ X เป็น ..." ให้ใช้ข้อความหลังคำว่า "เป็น" แทนข้อ X โดยตรงให้มากที่สุด
- ห้ามเติมคำขึ้นต้นใหม่ถ้าผู้ใช้ไม่ได้ระบุ
- ห้ามเปลี่ยนความหมายของข้อความที่ผู้ใช้ตั้งใจแก้
- แก้เฉพาะข้อที่ผู้ใช้สั่งแก้
- คงข้ออื่นที่ผู้ใช้ไม่ได้สั่งแก้ไว้
- ถ้าผู้ใช้สั่งลบ ให้ลบเฉพาะข้อที่ระบุ
- ถ้าผู้ใช้สั่งเพิ่มหรือแทรก ให้เพิ่มหรือแทรกในตำแหน่งที่เหมาะสม
- หลังแก้ไขแล้ว ให้เรียงเลขหรือหัวข้อใหม่ให้ถูกต้อง

รูปแบบคำตอบ:
- ตอบเป็นภาษาไทย
- แสดง {item['label_th']} ฉบับปรับปรุงแล้วทั้งหมด ไม่ใช่เฉพาะข้อที่แก้
- ไม่ต้องอธิบายกระบวนการคิด
"""


def call_gpt(client, model, prompt, temperature=0.7):
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=temperature,
    )
    return response.choices[0].message.content.strip()


def init_marketing_state(st):
    if "marketing_plan" not in st.session_state:
        st.session_state.marketing_plan = {
            "target_market": "",
            "customer_persona": "",
            "positioning": "",
            "marketing_mix": "",
            "sales_channels": "",
            "promotion_plan": "",
            "marketing_kpi": "",
        }
    if "marketing_current_item" not in st.session_state:
        st.session_state.marketing_current_item = None
    if "marketing_substage" not in st.session_state:
        st.session_state.marketing_substage = None
    if "marketing_draft" not in st.session_state:
        st.session_state.marketing_draft = ""


def start_marketing_workflow(st):
    st.session_state.stage = "marketing_plan"
    st.session_state.marketing_current_item = "target_market"
    st.session_state.marketing_substage = "input_or_request_suggestion"
    st.session_state.marketing_draft = ""
    return get_marketing_intro_prompt("target_market")


def move_to_next_marketing_item_or_finish(st, current_item):
    confirmed_content = st.session_state.marketing_draft.strip()
    if confirmed_content:
        st.session_state.marketing_plan[current_item] = confirmed_content

    next_item = MARKETING_ITEMS[current_item]["next"]

    if next_item:
        st.session_state.marketing_current_item = next_item
        st.session_state.marketing_substage = "input_or_request_suggestion"
        st.session_state.marketing_draft = ""
        return (
            f"✅ ผมได้บันทึก **{MARKETING_ITEMS[current_item]['label_th']} ({MARKETING_ITEMS[current_item]['label_en']})** ที่คุณยืนยันแล้วเรียบร้อยครับ\n\n"
            + get_marketing_intro_prompt(next_item)
        )

    st.session_state.stage = "financial_ready"
    st.session_state.marketing_current_item = None
    st.session_state.marketing_substage = None
    st.session_state.marketing_draft = ""

    return (
        f"✅ ผมได้บันทึก **{MARKETING_ITEMS[current_item]['label_th']} "
        f"({MARKETING_ITEMS[current_item]['label_en']})** ที่คุณยืนยันแล้วเรียบร้อยครับ\n\n"
        "✅ Marketing Plan เสร็จสมบูรณ์แล้วครับ\n\n"
        "ขั้นตอนต่อไปคือ **Financial Analysis**\n\n"
        "กรุณากดปุ่ม **💰 Financial Analysis (Input / Revise)** "
        "เพื่อจัดทำประมาณการทางการเงินครับ"
    )


def process_marketing_workflow(st, client, model, message, plan_data, strategic_analysis="", vision_mission_objectives=None, strategy_matrix=""):
    item_key = st.session_state.marketing_current_item
    substage = st.session_state.marketing_substage

    if not item_key:
        st.session_state.marketing_current_item = "target_market"
        st.session_state.marketing_substage = "input_or_request_suggestion"
        st.session_state.marketing_draft = ""
        return get_marketing_intro_prompt("target_market")

    item = MARKETING_ITEMS[item_key]

    if substage == "input_or_request_suggestion":
        if is_requesting_suggestion(message):
            prompt = get_initial_marketing_prompt(item_key, plan_data, strategic_analysis, vision_mission_objectives, strategy_matrix)
            draft = call_gpt(client, model, prompt)
            st.session_state.marketing_draft = draft
            st.session_state.marketing_substage = "review_draft"
            return (
                f"ผมขอเสนอ **{item['label_th']} ({item['label_en']})** จากข้อมูลธุรกิจ กลยุทธ์ และวัตถุประสงค์ดังนี้ครับ\n\n"
                f"{draft}" + get_marketing_review_menu(item_key)
            )

        st.session_state.marketing_draft = message
        st.session_state.marketing_substage = "review_draft"
        return (
            f"ผมได้รับ **{item['label_th']} ({item['label_en']})** ที่คุณระบุแล้วครับ\n\n"
            f"{message}" + get_marketing_review_menu(item_key)
        )

    if substage == "review_draft":
        if not st.session_state.marketing_draft.strip():
            st.session_state.marketing_substage = "input_or_request_suggestion"
            return get_marketing_intro_prompt(item_key)

        if is_go_next(message):
            return move_to_next_marketing_item_or_finish(st, item_key)

        if is_requesting_suggestion(message):
            prompt = get_enhance_marketing_prompt(item_key, st.session_state.marketing_draft, plan_data, strategic_analysis, vision_mission_objectives, strategy_matrix)
            revised = call_gpt(client, model, prompt)
            st.session_state.marketing_draft = revised
            return (
                f"ผมได้ช่วยทบทวนและปรับปรุง **{item['label_th']} ({item['label_en']})** ให้สอดคล้องกับกลยุทธ์มากขึ้นแล้วครับ\n\n"
                f"{revised}" + get_marketing_review_menu(item_key)
            )

        if is_empty_revision_request(message):
            return (
                f"ได้ครับ กรุณาพิมพ์คำสั่งที่ต้องการแก้ไข **{item['label_th']} ({item['label_en']})** ให้ชัดเจนขึ้น เช่น\n\n"
                "- ลบข้อ 3\n"
                "- แก้ข้อ 2 ให้เน้นลูกค้ากลุ่มครอบครัวผู้สูงอายุ\n"
                "- เพิ่มช่องทาง TikTok และ LINE OA\n"
                "- แทรกข้อใหม่ระหว่างข้อ 2 และข้อ 3\n\n"
                "เมื่อคุณพิมพ์คำสั่งแล้ว Chatbot จะช่วยแก้จากข้อความเดิมให้ โดยคุณไม่ต้องพิมพ์ทั้งหมดใหม่ครับ"
            )

        prompt = get_revise_marketing_prompt(item_key, st.session_state.marketing_draft, message, plan_data, strategic_analysis, vision_mission_objectives, strategy_matrix)
        revised = call_gpt(client, model, prompt)
        st.session_state.marketing_draft = revised
        return (
            f"ผมได้ปรับปรุง **{item['label_th']} ({item['label_en']})** ตามคำสั่งของคุณแล้วครับ\n\n"
            f"{revised}" + get_marketing_review_menu(item_key)
        )

    st.session_state.marketing_substage = "input_or_request_suggestion"
    st.session_state.marketing_draft = ""
    return get_marketing_intro_prompt(item_key)
