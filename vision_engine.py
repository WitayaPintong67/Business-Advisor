


# =========================================================
# Vision Engine for Smart Business Advisor
# Purpose:
# 1) Generate Vision / Mission / Objectives
# 2) Use iterative working draft workflow
# 3) Allow user to edit, add, delete, ask AI suggestion, and confirm
# =========================================================


VLO_ITEMS = {
    "vision": {
        "label_th": "วิสัยทัศน์",
        "label_en": "Vision",
        "next": "mission",
        "description": "ภาพอนาคตที่ธุรกิจต้องการเป็นในระยะยาว",
    },
    "mission": {
        "label_th": "พันธกิจ",
        "label_en": "Mission",
        "next": "objectives",
        "description": "บทบาท หน้าที่ และสิ่งที่ธุรกิจต้องทำเพื่อไปสู่วิสัยทัศน์",
    },
    "objectives": {
        "label_th": "วัตถุประสงค์",
        "label_en": "Objectives",
        "next": None,
        "description": "เป้าหมายที่ชัดเจน วัดผลได้ และสอดคล้องกับกลยุทธ์",
    },
}


def normalize_text(text):
    return text.strip().lower()


def is_requesting_suggestion(text):
    t = normalize_text(text)
    keywords = [
        "ช่วยคิด",
        "ช่วยแนะนำ",
        "แนะนำ",
        "เสนอ",
        "ขอคำแนะนำ",
        "ตัวอย่าง",
        "คิดให้",
        "suggest",
        "recommend",
        "example",
    ]
    return any(k in t for k in keywords)


def is_go_next(text):
    t = normalize_text(text)

    # กันกรณีที่ user ขอคำแนะนำ ไม่ใช่สั่งไปขั้นต่อไป
    negative_patterns = [
        "แนะนำ",
        "ขอคำแนะนำ",
        "ช่วยแนะนำ",
        "suggest",
        "recommend",
        "example",
        "ตัวอย่าง",
    ]

    if any(p in t for p in negative_patterns):
        return False

    next_patterns = [
        "ต่อไป",
        "ขั้นต่อไป",
        "ทำต่อ",
        "ทำต่อไป",
        "ทำขั้นต่อไป",
        "ช่วยทำต่อ",
        "ช่วยทำต่อไป",
        "ช่วยทำขั้นต่อไป",
        "ไปต่อ",
        "ไปขั้นต่อไป",
        "ดำเนินการต่อ",
        "ดำเนินขั้นต่อไป",
        "next",
        "continue",
    ]

    confirm_patterns = [
        "ไม่แก้",
        "ไม่แก้ไข",
        "พอแล้ว",
        "เสร็จแล้ว",
        "ยืนยัน",
        "ใช้ได้",
        "ตามนี้",
        "โอเค",
        "ok",
    ]

    return (
        any(p in t for p in next_patterns)
        or any(t == p or t.startswith(p) for p in confirm_patterns)
    )


def is_empty_revision_request(text):
    t = normalize_text(text)
    words = [
        "แก้",
        "แก้ไข",
        "เพิ่มเติม",
        "แก้ไขเพิ่มเติม",
        "ลบ",
        "ปรับปรุง",
        "edit",
        "revise",
    ]
    return t in words


def build_context(plan_data, strategic_analysis=""):
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
"""


def get_vlo_intro_prompt(item_key):
    item = VLO_ITEMS[item_key]

    if item_key == "vision":
        guide = (
            "วิสัยทัศน์ควรเป็นข้อความสั้น กระชับ สะท้อนภาพอนาคตที่ธุรกิจต้องการเป็น "
            "และควรเชื่อมโยงกับ SWOT Strategic Analysis"
        )
    elif item_key == "mission":
        guide = (
            "พันธกิจควรอธิบายว่าธุรกิจมีบทบาทอะไร ให้คุณค่าแก่ลูกค้าอย่างไร "
            "และต้องทำอะไรเพื่อไปสู่วิสัยทัศน์"
        )
    else:
        guide = (
            "วัตถุประสงค์ควรเป็นแบบ SMART คือ Specific, Measurable, Achievable, Relevant, Time-bound "
            "และควรแบ่งเป็นด้านการเงิน การตลาด การดำเนินงาน และการพัฒนาองค์กรได้"
        )

    return (
        f"ขั้นตอนต่อไปคือการจัดทำ **{item['label_th']} ({item['label_en']})**\n\n"
        f"{guide}\n\n"
        f"คุณสามารถพิมพ์ {item['label_th']} ที่คุณคิดไว้เองได้เลยครับ\n\n"
        f"หรือถ้าต้องการให้ Chatbot ช่วยเสนอ {item['label_th']} จาก Business Info, SWOT และ SWOT Strategic Analysis "
        f"ให้พิมพ์ว่า **ช่วยแนะนำ{item['label_th']}ให้หน่อย** ได้เลยครับ"
    )


def get_vlo_review_menu(item_key):
    item = VLO_ITEMS[item_key]

    return (
        f"\n\nโปรดตรวจสอบ **{item['label_th']} ({item['label_en']})** ข้างต้นครับ\n\n"
        "จากนั้นคุณสามารถเลือกทำอย่างใดอย่างหนึ่งต่อไปนี้:\n\n"
        "1. พิมพ์คำสั่ง **แก้ไข/เพิ่มเติม/ลบ** เช่น\n"
        "   - ปรับให้สั้นลง\n"
        "   - เพิ่มเรื่องนวัตกรรมและความยั่งยืน\n"
        "   - แก้ข้อ 2 ให้เน้นลูกค้ากลุ่มผู้สูงอายุ\n\n"
        "2. พิมพ์ว่า **ขอคำแนะนำ** ถ้าต้องการให้ Chatbot ช่วยปรับปรุงหรือเสนอแนวคิดเพิ่มเติม\n\n"
        "3. พิมพ์ว่า **ทำขั้นต่อไป** หรือ **ต่อไป** ถ้าพอใจแล้วและต้องการไปขั้นตอนถัดไป"
    )


def get_initial_vlo_prompt(item_key, plan_data, strategic_analysis=""):
    item = VLO_ITEMS[item_key]
    context = build_context(plan_data, strategic_analysis)

    if item_key == "vision":
        task = """
โปรดเสนอ Vision 2-3 ทางเลือก แล้วแนะนำทางเลือกที่เหมาะสมที่สุด 1 ข้อ
Vision ควรสั้น กระชับ มีพลัง และสะท้อนภาพอนาคตของธุรกิจ
"""
    elif item_key == "mission":
        task = """
โปรดเสนอ Mission ที่ประกอบด้วย 3-5 ข้อ
Mission ควรอธิบายว่าธุรกิจให้คุณค่าอะไรแก่ลูกค้า ทำอะไร และทำเพื่อใคร
"""
    else:
        task = """
โปรดเสนอ Objectives แบบ SMART โดยจัดเป็น 4 กลุ่ม:
1. Financial Objectives
2. Marketing Objectives
3. Operational Objectives
4. Learning & Growth Objectives

แต่ละ objective ควรมีเป้าหมายและกรอบเวลาเท่าที่เหมาะสม
"""

    return f"""
คุณคือที่ปรึกษาการจัดทำแผนธุรกิจระดับ MBA

ข้อมูลพื้นฐาน:
{context}

ขณะนี้ต้องการจัดทำ {item['label_th']} ({item['label_en']})

งานของคุณ:
{task}

เงื่อนไข:
- ตอบเป็นภาษาไทย
- ให้สอดคล้องกับ Business Info, SWOT และ SWOT Strategic Analysis
- อย่าเสนอสิ่งที่ขัดกับข้อมูลเดิม
- แสดงเฉพาะเนื้อหา {item['label_th']} ที่เสนอเท่านั้น
"""


def get_enhance_vlo_prompt(item_key, current_draft, plan_data, strategic_analysis=""):
    item = VLO_ITEMS[item_key]
    context = build_context(plan_data, strategic_analysis)

    return f"""
คุณคือที่ปรึกษาการจัดทำแผนธุรกิจและผู้ช่วยทบทวนข้อความเชิงกลยุทธ์

ข้อมูลพื้นฐาน:
{context}

ขณะนี้ผู้ใช้กำลังทบทวน {item['label_th']} ({item['label_en']})

{item['label_th']} ฉบับปัจจุบัน:
{current_draft}

งานของคุณ:
1. คงสาระเดิมของผู้ใช้ไว้ให้มากที่สุด
2. ช่วยปรับให้ชัดเจน มีเหตุผล และสอดคล้องกับ SWOT Strategic Analysis มากขึ้น
3. ถ้ามีประเด็นสำคัญที่ขาดไป ให้เพิ่มอย่างเหมาะสม
4. อย่าเขียนยาวเกินจำเป็น

รูปแบบคำตอบ:
- ตอบเป็นภาษาไทย
- แสดงเฉพาะ {item['label_th']} ฉบับปรับปรุงแล้วเท่านั้น
- ไม่ต้องอธิบายกระบวนการคิด
"""


def get_revise_vlo_prompt(item_key, current_draft, user_instruction, plan_data, strategic_analysis=""):
    item = VLO_ITEMS[item_key]
    context = build_context(plan_data, strategic_analysis)

    return f"""
คุณคือผู้ช่วยแก้ไขข้อความเชิงกลยุทธ์อย่างแม่นยำ

ข้อมูลพื้นฐาน:
{context}

ขณะนี้ผู้ใช้กำลังแก้ไข {item['label_th']} ({item['label_en']})

{item['label_th']} ฉบับปัจจุบัน:
{current_draft}

คำสั่งแก้ไขจากผู้ใช้:
{user_instruction}

งานของคุณ:
- ตีความคำสั่งของผู้ใช้ เช่น ลบ แก้ เพิ่ม ปรับถ้อยคำ ทำให้สั้นลง หรือทำให้ชัดเจนขึ้น
- แก้จากข้อความฉบับปัจจุบัน โดยไม่ต้องให้ผู้ใช้พิมพ์ใหม่ทั้งหมด
- คงประเด็นเดิมที่ผู้ใช้ไม่ได้สั่งแก้ไว้
- ทำให้ข้อความสอดคล้องกับ Business Info, SWOT และ SWOT Strategic Analysis

รูปแบบคำตอบ:
- ตอบเป็นภาษาไทย
- แสดงเฉพาะ {item['label_th']} ฉบับปรับปรุงแล้วเท่านั้น
- ไม่ต้องอธิบายกระบวนการคิด
"""


def call_gpt(client, model, prompt, temperature=0.7):
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=temperature,
    )
    return response.choices[0].message.content.strip()


def init_vlo_state(st):
    """
    Initialize Streamlit session_state variables for Vision/Mission/Objectives workflow.
    Call this from chat_business_plan4.py after general session initialization.
    """

    if "vlo_current_item" not in st.session_state:
        st.session_state.vlo_current_item = None

    if "vlo_substage" not in st.session_state:
        st.session_state.vlo_substage = None

    if "vlo_draft" not in st.session_state:
        st.session_state.vlo_draft = ""

    if "vision_mission_objectives" not in st.session_state:
        st.session_state.vision_mission_objectives = {
            "vision": "",
            "mission": "",
            "objectives": "",
        }


def start_vlo_workflow(st):
    """
    Start Vision/Mission/Objectives workflow.
    """

    st.session_state.stage = "vision_mission_objectives"
    st.session_state.vlo_current_item = "vision"
    st.session_state.vlo_substage = "input_or_request_suggestion"
    st.session_state.vlo_draft = ""

    return get_vlo_intro_prompt("vision")


def move_to_next_vlo_item_or_finish(st, current_item):
    """
    Save current V/M/O draft and move to next item.
    If all finished, move to strategy_ready.
    """

    confirmed_content = st.session_state.vlo_draft.strip()
    if confirmed_content:
        st.session_state.vision_mission_objectives[current_item] = confirmed_content

    next_item = VLO_ITEMS[current_item]["next"]

    if next_item:
        st.session_state.vlo_current_item = next_item
        st.session_state.vlo_substage = "input_or_request_suggestion"
        st.session_state.vlo_draft = ""

        return (
            f"✅ ผมได้บันทึก **{VLO_ITEMS[current_item]['label_th']} "
            f"({VLO_ITEMS[current_item]['label_en']})** ที่คุณยืนยันแล้วเรียบร้อยครับ\n\n"
            + get_vlo_intro_prompt(next_item)
        )

    st.session_state.stage = "strategy_ready"
    st.session_state.vlo_current_item = None
    st.session_state.vlo_substage = None
    st.session_state.vlo_draft = ""

    return (
        f"✅ ผมได้บันทึก **{VLO_ITEMS[current_item]['label_th']} "
        f"({VLO_ITEMS[current_item]['label_en']})** ที่คุณยืนยันแล้วเรียบร้อยครับ\n\n"
        "ตอนนี้เราได้จัดทำ Vision, Mission และ Objectives ครบแล้วครับ\n\n"
        "ขั้นตอนต่อไปคือการจัดทำ **Strategy Matrix (SO/ST/WO/WT)** "
        "โดยจะเชื่อมโยงกลยุทธ์กับ SWOT Strategic Analysis อย่างชัดเจน"
    )


def process_vlo_workflow(st, client, model, message, plan_data, strategic_analysis=""):
    """
    Main workflow handler for Vision/Mission/Objectives.
    """

    item_key = st.session_state.vlo_current_item
    substage = st.session_state.vlo_substage

    if not item_key:
        st.session_state.vlo_current_item = "vision"
        st.session_state.vlo_substage = "input_or_request_suggestion"
        st.session_state.vlo_draft = ""
        return get_vlo_intro_prompt("vision")

    item = VLO_ITEMS[item_key]

    if substage == "input_or_request_suggestion":
        if is_requesting_suggestion(message):
            prompt = get_initial_vlo_prompt(
                item_key=item_key,
                plan_data=plan_data,
                strategic_analysis=strategic_analysis,
            )
            draft = call_gpt(client, model, prompt)
            st.session_state.vlo_draft = draft
            st.session_state.vlo_substage = "review_draft"

            return (
                f"ผมขอเสนอ **{item['label_th']} ({item['label_en']})** จาก Business Info, SWOT และ SWOT Strategic Analysis ดังนี้ครับ\n\n"
                f"{draft}"
                + get_vlo_review_menu(item_key)
            )

        st.session_state.vlo_draft = message
        st.session_state.vlo_substage = "review_draft"

        return (
            f"ผมได้รับ **{item['label_th']} ({item['label_en']})** ที่คุณระบุแล้วครับ\n\n"
            f"{message}"
            + get_vlo_review_menu(item_key)
        )

    if substage == "review_draft":
        if not st.session_state.vlo_draft.strip():
            st.session_state.vlo_substage = "input_or_request_suggestion"
            return get_vlo_intro_prompt(item_key)

        if is_go_next(message):
            return move_to_next_vlo_item_or_finish(st, item_key)

        if is_requesting_suggestion(message):
            prompt = get_enhance_vlo_prompt(
                item_key=item_key,
                current_draft=st.session_state.vlo_draft,
                plan_data=plan_data,
                strategic_analysis=strategic_analysis,
            )
            revised = call_gpt(client, model, prompt)
            st.session_state.vlo_draft = revised

            return (
                f"ผมได้ช่วยทบทวนและปรับปรุง **{item['label_th']} ({item['label_en']})** ให้สอดคล้องกับ SWOT Strategic Analysis มากขึ้นแล้วครับ\n\n"
                f"{revised}"
                + get_vlo_review_menu(item_key)
            )

        if is_empty_revision_request(message):
            return (
                f"ได้ครับ กรุณาพิมพ์คำสั่งที่ต้องการแก้ไข **{item['label_th']} ({item['label_en']})** ให้ชัดเจนขึ้น เช่น\n\n"
                "- ปรับให้สั้นลง\n"
                "- เพิ่มเรื่องนวัตกรรมและความยั่งยืน\n"
                "- แก้ข้อ 2 ให้เน้นลูกค้ากลุ่มผู้สูงอายุ\n\n"
                "เมื่อคุณพิมพ์คำสั่งแล้ว Chatbot จะช่วยแก้จากข้อความเดิมให้ โดยคุณไม่ต้องพิมพ์ทั้งหมดใหม่ครับ"
            )

        prompt = get_revise_vlo_prompt(
            item_key=item_key,
            current_draft=st.session_state.vlo_draft,
            user_instruction=message,
            plan_data=plan_data,
            strategic_analysis=strategic_analysis,
        )
        revised = call_gpt(client, model, prompt)
        st.session_state.vlo_draft = revised

        return (
            f"ผมได้ปรับปรุง **{item['label_th']} ({item['label_en']})** ตามคำสั่งของคุณแล้วครับ\n\n"
            f"{revised}"
            + get_vlo_review_menu(item_key)
        )

    st.session_state.vlo_substage = "input_or_request_suggestion"
    st.session_state.vlo_draft = ""
    return get_vlo_intro_prompt(item_key)
