import streamlit as st
 
import openai
import json

from strategic_engine import (
    build_swot_context,
    get_strategic_analysis_prompt,
    get_strategy_matrix_prompt,
    process_strategic_analysis,
    process_strategy_matrix
)
from vision_engine import (
    normalize_text,
    is_requesting_suggestion,
    is_go_next,
    is_empty_revision_request,
    build_context,
    get_vlo_intro_prompt,
    get_vlo_review_menu,
    get_initial_vlo_prompt,
    get_enhance_vlo_prompt,
    get_revise_vlo_prompt,
    call_gpt,
    init_vlo_state,
    start_vlo_workflow,
    move_to_next_vlo_item_or_finish,
    process_vlo_workflow
)


from planner import get_financial_step_prompt
from exporter import export_to_docx
from financial_engine import calculate_financials

# =========================================================
# Page Config + OpenAI Client
# =========================================================
st.set_page_config(layout="wide")

OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]
client = openai.OpenAI(api_key=OPENAI_API_KEY)


# =========================================================
# Constants
# =========================================================
SWOT_ITEMS = {
    "strengths": {
        "label_th": "จุดแข็ง",
        "label_en": "Strengths",
        "next": "weaknesses",
        "examples": "ความสามารถหลัก จุดเด่นของสินค้า/บริการ ทรัพยากรที่มี ความเชี่ยวชาญ หรือความได้เปรียบเหนือคู่แข่ง",
    },
    "weaknesses": {
        "label_th": "จุดอ่อน",
        "label_en": "Weaknesses",
        "next": "opportunities",
        "examples": "ข้อจำกัดด้านเงินทุน บุคลากร ระบบงาน เทคโนโลยี ประสบการณ์ หรือข้อเสียเปรียบเมื่อเทียบกับคู่แข่ง",
    },
    "opportunities": {
        "label_th": "โอกาส",
        "label_en": "Opportunities",
        "next": "threats",
        "examples": "แนวโน้มตลาด ความต้องการของลูกค้า เทคโนโลยีใหม่ นโยบายภาครัฐ หรือช่องทางการเติบโต",
    },
    "threats": {
        "label_th": "ภัยคุกคาม",
        "label_en": "Threats",
        "next": None,
        "examples": "คู่แข่ง ภาวะเศรษฐกิจ ต้นทุนที่เพิ่มขึ้น การเปลี่ยนแปลงของลูกค้า กฎหมาย หรือความเสี่ยงภายนอก",
    },
}


# =========================================================
# Session State Initialization
# =========================================================
def init_session_state():
    if "chat_log" not in st.session_state:
        st.session_state.chat_log = [
            {
                "role": "system",
                "content": (
                    "You are a business plan advisor. "
                    "Guide the user step by step through Business Info, SWOT, Vision, Mission, Objectives, "
                    "Strategy, Marketing, Financial Analysis, and Executive Summary. "
                    "Be supportive, practical, and ask for the next required input clearly."
                ),
            }
        ]

    if "stage" not in st.session_state:
        st.session_state.stage = "not_started"

    if "plan_data" not in st.session_state:
        st.session_state.plan_data = {
            "business_info": "",
            "strengths": "",
            "weaknesses": "",
            "opportunities": "",
            "threats": "",
        }

    # SWOT workflow state
    if "swot_current_item" not in st.session_state:
        st.session_state.swot_current_item = None

    if "swot_substage" not in st.session_state:
        # possible values:
        # input_or_request_suggestion
        # review_draft
        st.session_state.swot_substage = None

    # This is the working draft for the current SWOT item.
    # It may come from the user, from GPT, or from GPT-revised user instructions.
    if "swot_draft" not in st.session_state:
        st.session_state.swot_draft = ""

    # Kept for compatibility with old saved project files
    if "swot_pending_suggestion" not in st.session_state:
        st.session_state.swot_pending_suggestion = ""

    # Strategic Analysis state
    if "strategic_analysis" not in st.session_state:
        st.session_state.strategic_analysis = ""

    # Vision / Mission / Objectives state
    if "vision_mission_objectives" not in st.session_state:
        st.session_state.vision_mission_objectives = {
            "vision": "",
            "mission": "",
            "objectives": "",
        }

    if "vlo_current_item" not in st.session_state:
        st.session_state.vlo_current_item = None

    if "vlo_substage" not in st.session_state:
        st.session_state.vlo_substage = None

    if "vlo_draft" not in st.session_state:
        st.session_state.vlo_draft = ""

    if "strategy_matrix" not in st.session_state:
        st.session_state.strategy_matrix = ""        


    if "financial_step" not in st.session_state:
        st.session_state.financial_step = 0

    if "financial_inputs" not in st.session_state:
        st.session_state.financial_inputs = {}

    if "financial_file" not in st.session_state:
        st.session_state.financial_file = None

    # ใช้บอกว่า user กำลังกรอก/แก้ไขข้อมูล Financial Analysis
    if "financial_mode" not in st.session_state:
        st.session_state.financial_mode = "new"  
        # possible values: "new", "revise"

    # ใช้เก็บสถานะว่าเคยคำนวณ Financial Analysis แล้วหรือยัง
    if "financial_completed" not in st.session_state:
        st.session_state.financial_completed = False

    if "user_input" not in st.session_state:
        st.session_state.user_input = ""


init_session_state()


# =========================================================
# Helper Functions
# =========================================================
def ask_gpt(prompt, use_chat_history=False):
    if use_chat_history:
        messages = st.session_state.chat_log + [{"role": "user", "content": prompt}]
    else:
        messages = [{"role": "user", "content": prompt}]

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        temperature=0.7,
    )

    return response.choices[0].message.content.strip()


def append_assistant(content):
    st.session_state.chat_log.append({"role": "assistant", "content": content})


def append_user(content):
    st.session_state.chat_log.append({"role": "user", "content": content})


def normalize_text(text):
    return text.strip().lower()


def is_requesting_example(text):
    t = normalize_text(text)
    keywords = [
        "ตัวอย่าง",
        "ช่วยคิด",
        "ช่วยแนะนำ",
        "แนะนำ",
        "ยกตัวอย่าง",
        "ช่วยเสนอ",
        "คิดให้",
        "เสนอให้",
        "ขอคำแนะนำ",
        "แนะนำเพิ่ม",
        "แนะนำเพิ่มเติม",
        "ช่วยดู",
        "suggest",
        "example",
        "recommend",
    ]
    return any(k in t for k in keywords)


def is_go_next(text):
    t = normalize_text(text)
    next_words = [
        "ต่อไป",
        "ทำขั้นต่อไป",
        "ขั้นต่อไป",
        "ไปต่อ",
        "ไม่แก้ไข",
        "ไม่แก้",
        "พอแล้ว",
        "เสร็จแล้ว",
        "ยืนยัน",
        "ใช้ได้",
        "ตามนี้",
        "next",
        "continue",
    ]
    return any(t == w or t.startswith(w) for w in next_words)


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


def get_swot_intro_prompt(item_key):
    item = SWOT_ITEMS[item_key]
    return (
        f"กรุณาระบุ **{item['label_th']} ({item['label_en']})** ของธุรกิจนี้\n\n"
        f"ตัวอย่างประเด็นที่อาจพิจารณา ได้แก่ {item['examples']}\n\n"
        f"ถ้าคุณมีข้อมูลอยู่แล้ว สามารถพิมพ์ {item['label_th']} เป็นข้อ ๆ ได้เลยครับ\n\n"
        f"แต่ถ้าต้องการให้ Chatbot ช่วยแนะนำ {item['label_th']} จากข้อมูลธุรกิจเบื้องต้น "
        f"ให้พิมพ์ว่า **ช่วยแนะนำ{item['label_th']}ให้หน่อย** ได้เลยครับ"
    )


def get_swot_review_menu(item_key):
    item = SWOT_ITEMS[item_key]
    return (
        f"\n\nโปรดตรวจสอบ **{item['label_th']} ({item['label_en']})** ข้างต้นครับ\n\n"
        "จากนั้นคุณสามารถเลือกทำอย่างใดอย่างหนึ่งต่อไปนี้:\n\n"
        "1. พิมพ์คำสั่ง **แก้ไข/เพิ่มเติม/ลบ** เช่น\n"
        "   - ลบข้อ 3\n"
        "   - แก้ข้อ 2 ให้เน้นความเชี่ยวชาญของบุคลากร\n"
        "   - เพิ่มเรื่องทำเลใกล้โรงพยาบาล\n\n"
        "2. พิมพ์ว่า **ขอคำแนะนำ** ถ้าต้องการให้ Chatbot ช่วยเสนอประเด็นเพิ่มเติม โดยจะคงของเดิมไว้และเพิ่มเฉพาะประเด็นที่ยังขาด\n\n"
        "3. พิมพ์ว่า **ทำขั้นต่อไป** หรือ **ต่อไป** ถ้าพอใจแล้วและต้องการไป SWOT ตัวถัดไป"
    )


def get_next_swot_item(item_key):
    return SWOT_ITEMS[item_key]["next"]


def generate_initial_swot_suggestion(item_key):
    item = SWOT_ITEMS[item_key]
    business_info = st.session_state.plan_data.get("business_info", "")
    strengths = st.session_state.plan_data.get("strengths", "")
    weaknesses = st.session_state.plan_data.get("weaknesses", "")
    opportunities = st.session_state.plan_data.get("opportunities", "")
    threats = st.session_state.plan_data.get("threats", "")

    prompt = f"""
คุณคือที่ปรึกษาการจัดทำแผนธุรกิจ

จากข้อมูลธุรกิจต่อไปนี้:
{business_info}

ข้อมูล SWOT ที่ผู้ใช้ยืนยันแล้วก่อนหน้านี้:
Strengths:
{strengths}

Weaknesses:
{weaknesses}

Opportunities:
{opportunities}

Threats:
{threats}

โปรดช่วยเสนอ {item['label_th']} ({item['label_en']}) สำหรับธุรกิจนี้ จำนวน 5-8 ข้อ

เงื่อนไข:
- ตอบเป็นภาษาไทย
- เขียนเป็นรายการ numbered list
- ให้เหมาะกับการนำไปใช้ใน SWOT Analysis
- อย่าเขียนยาวเกินไป
- อย่าใส่ Vision, Mission, Objectives หรือ Strategy ในคำตอบนี้
- แสดงเฉพาะรายการ {item['label_th']} เท่านั้น
"""

    return ask_gpt(prompt, use_chat_history=False)


def enhance_swot_draft_with_ai(item_key):
    item = SWOT_ITEMS[item_key]
    business_info = st.session_state.plan_data.get("business_info", "")
    current_draft = st.session_state.swot_draft
    strengths = st.session_state.plan_data.get("strengths", "")
    weaknesses = st.session_state.plan_data.get("weaknesses", "")
    opportunities = st.session_state.plan_data.get("opportunities", "")
    threats = st.session_state.plan_data.get("threats", "")

    prompt = f"""
คุณคือที่ปรึกษาการจัดทำแผนธุรกิจและผู้ช่วยทบทวน SWOT

ข้อมูลธุรกิจ:
{business_info}

ข้อมูล SWOT ที่ผู้ใช้ยืนยันแล้วก่อนหน้านี้:
Strengths:
{strengths}

Weaknesses:
{weaknesses}

Opportunities:
{opportunities}

Threats:
{threats}

ขณะนี้ผู้ใช้กำลังทำ {item['label_th']} ({item['label_en']})

{item['label_th']} ฉบับปัจจุบันที่ผู้ใช้กำลังทบทวน:
{current_draft}

งานของคุณ:
1. คงประเด็นเดิมของผู้ใช้ไว้ให้มากที่สุด
2. ตรวจสอบว่ามีประเด็นสำคัญใดที่ยังขาดหายไป
3. เพิ่มประเด็นใหม่ที่เหมาะสมอีกประมาณ 3-5 ข้อ
4. ถ้ามีข้อเดิมที่ซ้ำกันมาก ให้รวมให้กระชับได้
5. อย่าเปลี่ยนความหมายหลักของข้อความเดิมโดยไม่จำเป็น

รูปแบบคำตอบ:
- ตอบเป็นภาษาไทย
- เขียนเป็น numbered list ใหม่ทั้งหมด
- แสดงเฉพาะรายการ {item['label_th']} ฉบับปรับปรุงแล้วเท่านั้น
- ไม่ต้องอธิบายกระบวนการคิด
"""

    return ask_gpt(prompt, use_chat_history=False)


def revise_swot_draft_by_instruction(item_key, user_instruction):
    item = SWOT_ITEMS[item_key]
    business_info = st.session_state.plan_data.get("business_info", "")
    current_draft = st.session_state.swot_draft

    prompt = f"""
คุณคือผู้ช่วยแก้ไขข้อความ SWOT อย่างแม่นยำ

ข้อมูลธุรกิจ:
{business_info}

ขณะนี้ผู้ใช้กำลังทำ {item['label_th']} ({item['label_en']})

{item['label_th']} ฉบับปัจจุบัน:
{current_draft}

คำสั่งแก้ไขจากผู้ใช้:
{user_instruction}

งานของคุณ:
- ตีความคำสั่งของผู้ใช้ เช่น ลบข้อที่ระบุ แก้ข้อความข้อที่ระบุ เพิ่มข้อใหม่ หรือปรับถ้อยคำ
- แก้ไขจากข้อความฉบับปัจจุบัน ไม่ต้องให้ผู้ใช้พิมพ์ทั้งหมดใหม่
- คงประเด็นเดิมที่ผู้ใช้ไม่ได้สั่งแก้ไว้
- ถ้าผู้ใช้สั่งเพิ่ม ให้เพิ่มเข้าไปในรายการอย่างเป็นธรรมชาติ
- ถ้าผู้ใช้สั่งลบ ให้ลบเฉพาะข้อที่ระบุ
- ถ้าผู้ใช้สั่งแก้ ให้แก้เฉพาะข้อที่เกี่ยวข้อง
- เรียงเลขรายการใหม่ให้ถูกต้อง

รูปแบบคำตอบ:
- ตอบเป็นภาษาไทย
- เขียนเป็น numbered list ใหม่ทั้งหมด
- แสดงเฉพาะรายการ {item['label_th']} ฉบับปรับปรุงแล้วเท่านั้น
- ไม่ต้องอธิบายกระบวนการคิด
"""

    return ask_gpt(prompt, use_chat_history=False)


def save_confirmed_swot_item(item_key, content):
    st.session_state.plan_data[item_key] = content


def move_to_next_swot_item_or_finish(current_item):
    current = SWOT_ITEMS[current_item]
    confirmed_content = st.session_state.swot_draft.strip()

    if confirmed_content:
        save_confirmed_swot_item(current_item, confirmed_content)

    next_item = get_next_swot_item(current_item)

    if next_item:
        st.session_state.swot_current_item = next_item
        st.session_state.swot_substage = "input_or_request_suggestion"
        st.session_state.swot_draft = ""

        return (
            f"✅ ผมได้บันทึก **{current['label_th']} ({current['label_en']})** ที่คุณยืนยันแล้วเรียบร้อยครับ\n\n"
            f"ขั้นต่อไปคือการวิเคราะห์ **{SWOT_ITEMS[next_item]['label_th']} "
            f"({SWOT_ITEMS[next_item]['label_en']})**\n\n"
            + get_swot_intro_prompt(next_item)
        )

    st.session_state.stage = "strategic_analysis"
    st.session_state.swot_current_item = None
    st.session_state.swot_substage = None
    st.session_state.swot_draft = ""

    return (
        f"✅ ผมได้บันทึก **{current['label_th']} ({current['label_en']})** ที่คุณยืนยันแล้วเรียบร้อยครับ\n\n"
        + generate_swot_summary()
        + "\n\n---\n\n"
        + "✅ SWOT Analysis เสร็จสมบูรณ์แล้วครับ\n\n"
        + "ขั้นตอนต่อไปคือ **SWOT Strategic Analysis**\n\n"
        + "กรุณาพิมพ์ว่า **ทำขั้นต่อไป** เพื่อให้ Chatbot วิเคราะห์ประเด็นเชิงกลยุทธ์จาก SWOT ที่ยืนยันแล้วครับ"
    )

def generate_swot_summary():
    prompt = f"""
โปรดสรุป SWOT Analysis จากข้อมูลต่อไปนี้เป็นภาษาไทย

สำคัญมาก:
- ใช้เฉพาะข้อมูลที่อยู่ใน Business Info, Strengths, Weaknesses, Opportunities และ Threats ด้านล่างนี้เท่านั้น
- ห้ามนำตัวอย่าง SWOT ที่เคยเสนอไว้ก่อนหน้านี้แต่ผู้ใช้ยังไม่ได้ยืนยันมาใช้
- จัดรูปแบบให้อ่านง่าย
- หลังจากสรุปแล้ว ให้บอกผู้ใช้ว่าขั้นต่อไปควรพัฒนา Vision, Mission และ Objectives

Business Info:
{st.session_state.plan_data["business_info"]}

Strengths:
{st.session_state.plan_data["strengths"]}

Weaknesses:
{st.session_state.plan_data["weaknesses"]}

Opportunities:
{st.session_state.plan_data["opportunities"]}

Threats:
{st.session_state.plan_data["threats"]}
"""

    return ask_gpt(prompt, use_chat_history=False)


def process_business_info(message):
    st.session_state.plan_data["business_info"] = message
    st.session_state.stage = "swot"
    st.session_state.swot_current_item = "strengths"
    st.session_state.swot_substage = "input_or_request_suggestion"
    st.session_state.swot_draft = ""

    return (
        "ขอบคุณครับ ผมได้รับข้อมูลธุรกิจเบื้องต้นแล้ว และได้บันทึกไว้ในระบบแล้ว\n\n"
        "ขั้นต่อไปคือการวิเคราะห์ SWOT โดยเริ่มจาก **จุดแข็ง (Strengths)**\n\n"
        + get_swot_intro_prompt("strengths")
    )


def process_swot_workflow(message):
    item_key = st.session_state.swot_current_item
    substage = st.session_state.swot_substage

    if not item_key:
        st.session_state.swot_current_item = "strengths"
        st.session_state.swot_substage = "input_or_request_suggestion"
        st.session_state.swot_draft = ""
        return get_swot_intro_prompt("strengths")

    item = SWOT_ITEMS[item_key]

    # 1) First entry for each SWOT item:
    # User may enter their own SWOT, or ask GPT to suggest.
    if substage == "input_or_request_suggestion":
        if is_requesting_example(message):
            draft = generate_initial_swot_suggestion(item_key)
            st.session_state.swot_draft = draft
            st.session_state.swot_substage = "review_draft"

            return (
                f"ผมขอเสนอ **{item['label_th']} ({item['label_en']})** จากข้อมูลธุรกิจเบื้องต้นดังนี้ครับ\n\n"
                f"{draft}"
                + get_swot_review_menu(item_key)
            )

        # User enters SWOT by themselves
        st.session_state.swot_draft = message
        st.session_state.swot_substage = "review_draft"

        return (
            f"ผมได้รับ **{item['label_th']} ({item['label_en']})** ที่คุณระบุแล้วครับ\n\n"
            f"{message}"
            + get_swot_review_menu(item_key)
        )

    # 2) Review stage:
    # User can ask GPT to add ideas, ask GPT to revise/delete/edit, or move next.
    if substage == "review_draft":
        if not st.session_state.swot_draft.strip():
            st.session_state.swot_substage = "input_or_request_suggestion"
            return get_swot_intro_prompt(item_key)

        if is_go_next(message):
            return move_to_next_swot_item_or_finish(item_key)

        if is_requesting_example(message):
            revised = enhance_swot_draft_with_ai(item_key)
            st.session_state.swot_draft = revised

            return (
                f"ผมได้ช่วยทบทวนและเสนอ **{item['label_th']} ({item['label_en']})** เพิ่มเติม โดยคงประเด็นเดิมไว้ให้มากที่สุดแล้วครับ\n\n"
                f"{revised}"
                + get_swot_review_menu(item_key)
            )

#        if is_empty_revision_request(message):
#            return (
#                f"ได้ครับ กรุณาพิมพ์คำสั่งที่ต้องการแก้ไข **{item['label_th']} ({item['label_en']})** ให้ชัดเจนขึ้น เช่น\n\n"
#                "- ลบข้อ 3\n"
#                "- แก้ข้อ 2 ให้เน้นความเชี่ยวชาญของบุคลากร\n"
#                "- เพิ่มเรื่องทำเลใกล้โรงพยาบาล\n\n"
#                "เมื่อคุณพิมพ์คำสั่งแล้ว Chatbot จะช่วยแก้จากข้อความเดิมให้ โดยคุณไม่ต้องพิมพ์ทั้งหมดใหม่ครับ"
#            )

        # Any other message in review stage is treated as a natural-language editing instruction
        revised = revise_swot_draft_by_instruction(item_key, message).strip()
        st.session_state.swot_draft = revised
        st.session_state.plan_data[item_key] = revised
        return (
            f"ผมได้ปรับปรุง **{item['label_th']} ({item['label_en']})** ตามคำสั่งของคุณแล้วครับ\n\n"
            f"{revised}"
            + get_swot_review_menu(item_key)
        )

    # Safety fallback
    st.session_state.swot_substage = "input_or_request_suggestion"
    st.session_state.swot_draft = ""
    return get_swot_intro_prompt(item_key)


# =========================================================
# Styling
# =========================================================

st.markdown("""
<style>
.block-container {
    padding-top: 1rem;
    max-width: 1400px;
}

.title-container {
    background: linear-gradient(135deg, #e8f3e8, #f7fbf7);
    padding: 32px;
    border-radius: 16px;
    margin-bottom: 24px;
    border: 1px solid #d6e6d6;
}

.header-assistant,
.header-user {
    padding: 14px;
    border-radius: 14px;
    font-weight: 700;
    font-size: 24px;
    margin-bottom: 14px;
}

.header-assistant {
    background-color: #eef7ed;
    color: #1f4d2b;
    border: 1px solid #cfe5cc;
}

.header-user {
    background-color: #eef5fb;
    color: #1d4566;
    border: 1px solid #cfe0ef;
}

.chat-message {
    background-color: #ffffff;
    font-size: 19px;
    line-height: 1.75;
    padding: 18px 20px;
    margin-bottom: 14px;
    border-radius: 16px;
    border: 1px solid #e6e6e6;
    box-shadow: 0 2px 8px rgba(0,0,0,0.04);
    word-wrap: break-word;
}

.assistant-message {
    background-color: #f7fbf7;
    border-left: 5px solid #7ab87a;
}

.user-message {
    background-color: #f7fbff;
    border-left: 5px solid #6fa8dc;
}

.chat-role {
    font-weight: 700;
    margin-bottom: 8px;
    font-size: 18px;
}

.chat-content {
    font-size: 19px;
    line-height: 1.8;
}

.chat-content p {
    margin-bottom: 0.8rem;
}

.chat-content ol,
.chat-content ul {
    padding-left: 1.5rem;
    margin-top: 0.4rem;
    margin-bottom: 0.8rem;
}

.chat-content li {
    margin-bottom: 0.35rem;
}
</style>
""", unsafe_allow_html=True)


# =========================================================
# Title
# =========================================================
st.markdown("""
<div class="title-container">
    <h1 style="text-align:center; font-size:46px;">💼 Dr. Witaya Chat Bot for Business Plan</h1>
    <p style="text-align:center; font-size:28px;">
    A smarter step-by-step business plan assistant
    </p>
</div>
""", unsafe_allow_html=True)


# =========================================================
# Main Buttons
# =========================================================
cols = st.columns(5)

with cols[0]:
    if st.button("▶️ Start / Continue Plan", use_container_width=True):
        if st.session_state.stage == "not_started":
            st.session_state.stage = "business_info"
            append_assistant(
                "ยินดีต้อนรับครับ เราจะจัดทำแผนธุรกิจตามขั้นตอนหลักดังนี้:\n\n"
                "1. Business Info\n"
                "2. SWOT Analysis\n"
                "3. Vision / Mission / Objectives\n"
                "4. Strategy\n"
                "5. Marketing Plan\n"
                "6. Financial Analysis\n"
                "7. Executive Summary\n\n"
                "ขั้นแรก กรุณาให้ข้อมูลธุรกิจเบื้องต้น เช่น\n"
                "- ชื่อธุรกิจ\n"
                "- ประเภทธุรกิจ\n"
                "- สินค้าหรือบริการ\n"
                "- กลุ่มลูกค้าเป้าหมาย\n"
                "- จุดเด่นหรือแนวคิดธุรกิจ"
            )
        elif st.session_state.stage == "swot":
            current_item = st.session_state.swot_current_item or "strengths"
            if st.session_state.swot_substage == "review_draft" and st.session_state.swot_draft:
                append_assistant(
                    f"ขณะนี้กำลังทบทวน **{SWOT_ITEMS[current_item]['label_th']} ({SWOT_ITEMS[current_item]['label_en']})** ฉบับร่างดังนี้ครับ\n\n"
                    f"{st.session_state.swot_draft}"
                    + get_swot_review_menu(current_item)
                )
            else:
                append_assistant(get_swot_intro_prompt(current_item))
        elif st.session_state.stage == "vision_ready":
            append_assistant(
                "ตอนนี้ SWOT Analysis เสร็จแล้วครับ\n\n"
                "ขั้นต่อไปคือการพัฒนา Vision, Mission และ Objectives "
                "จากข้อมูลธุรกิจและ SWOT ที่ได้ยืนยันไว้แล้ว"
            )
        st.rerun()

with cols[1]:
    if st.button("💰 Financial Analysis (Input / Revise)", use_container_width=True):
        st.session_state.stage = "financial"

        # ถ้ามีข้อมูลเดิมแล้ว ให้เริ่มที่ Step 1 พร้อมข้อมูลเดิม
        # user สามารถกด Next ผ่าน step ที่ไม่ต้องการแก้ได้
        st.session_state.financial_step = 1

        if st.session_state.get("financial_completed", False):
            st.session_state.financial_mode = "revise"
        else:
            st.session_state.financial_mode = "new"

        st.rerun()

with cols[2]:
    if st.button("💾 Save Project", use_container_width=True):
        data = {
            "chat_log": st.session_state.chat_log,
            "stage": st.session_state.stage,
            "plan_data": st.session_state.plan_data,
            "swot_current_item": st.session_state.swot_current_item,
            "swot_substage": st.session_state.swot_substage,
            "swot_draft": st.session_state.swot_draft,
            "swot_pending_suggestion": st.session_state.swot_pending_suggestion,
            "financial_inputs": st.session_state.financial_inputs,
        }
        with open("business_plan_project.json", "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        st.success("บันทึก Project แล้ว")

with cols[3]:
    if st.button("📂 Load Project", use_container_width=True):
        try:
            with open("business_plan_project.json", "r", encoding="utf-8") as f:
                data = json.load(f)

            st.session_state.chat_log = data.get("chat_log", st.session_state.chat_log)
            st.session_state.stage = data.get("stage", "not_started")
            st.session_state.plan_data = data.get("plan_data", st.session_state.plan_data)
            st.session_state.swot_current_item = data.get("swot_current_item", None)
            st.session_state.swot_substage = data.get("swot_substage", None)
            st.session_state.swot_draft = data.get("swot_draft", "")
            st.session_state.swot_pending_suggestion = data.get("swot_pending_suggestion", "")
            st.session_state.financial_inputs = data.get("financial_inputs", {})

            st.success("โหลด Project แล้ว")
            st.rerun()
        except FileNotFoundError:
            st.error("ยังไม่พบไฟล์ business_plan_project.json")

with cols[4]:
    if st.button("🔄 Reset", use_container_width=True):
        st.session_state.clear()
        st.rerun()

if st.button("📝 Export Report"):
    export_to_docx(st.session_state.chat_log)
    st.success("Export เป็น Word แล้ว")


# =========================================================
# Chat Display
# =========================================================
col_assist, col_you = st.columns(2)

with col_assist:
    st.markdown(
        '<div class="header-assistant" style="text-align:center;">🧠 Dr. Witaya</div>',
        unsafe_allow_html=True,
    )

    for msg in st.session_state.chat_log:
        if msg["role"] == "assistant":
            st.markdown('<div class="chat-message assistant-message">', unsafe_allow_html=True)
            st.markdown('<div class="chat-role">Dr. Witaya</div>', unsafe_allow_html=True)
            st.markdown(msg["content"])
            st.markdown('</div>', unsafe_allow_html=True)

with col_you:
    st.markdown(
        '<div class="header-user" style="text-align:center;">👤 You</div>',
        unsafe_allow_html=True,
    )

    for msg in st.session_state.chat_log:
        if msg["role"] == "user":
            st.markdown('<div class="chat-message user-message">', unsafe_allow_html=True)
            st.markdown('<div class="chat-role">You</div>', unsafe_allow_html=True)
            st.markdown(msg["content"])
            st.markdown('</div>', unsafe_allow_html=True)

# =========================================================
# Status + Input
# =========================================================
st.markdown("---")

status_extra = ""
if st.session_state.stage == "swot":
    status_extra = (
        f" | SWOT Item: `{st.session_state.swot_current_item}`"
        f" | Substage: `{st.session_state.swot_substage}`"
    )

st.markdown(f"📌 **Current Stage:** `{st.session_state.stage}`{status_extra}")

user_message = st.text_area("✏️ Type your message below", height=180, key="user_input")

if st.button("Send", use_container_width=True):
    message = st.session_state.user_input.strip()

    if message:
        append_user(message)
        current_stage = st.session_state.stage

        if current_stage == "business_info":
            reply = process_business_info(message)
            append_assistant(reply)

        elif current_stage == "swot":
            reply = process_swot_workflow(message)
            append_assistant(reply)


        elif current_stage == "strategic_analysis":
            analysis = process_strategic_analysis(
                client=client,
                model="gpt-4o-mini",
                plan_data=st.session_state.plan_data
            )

            st.session_state.strategic_analysis = analysis
            append_assistant(analysis)

            reply = start_vlo_workflow(st)
            append_assistant(reply)

        elif current_stage == "vision_mission_objectives":
            reply = process_vlo_workflow(
                st=st,
                client=client,
                model="gpt-4o-mini",
                message=message,
                plan_data=st.session_state.plan_data,
                strategic_analysis=st.session_state.strategic_analysis
            )
            append_assistant(reply)

        elif current_stage == "strategy_ready":
            vmo = st.session_state.vision_mission_objectives

            strategy = process_strategy_matrix(
                client=client,
                model="gpt-4o-mini",
                plan_data=st.session_state.plan_data,
                strategic_analysis=st.session_state.strategic_analysis,
                vision=vmo.get("vision", ""),
                mission=vmo.get("mission", ""),
                objectives=vmo.get("objectives", "")
            )

            st.session_state.strategy_matrix = strategy

            append_assistant(
                strategy
                + "\n\n---\n\n"
                + "✅ Strategy Matrix เสร็จแล้วครับ\n\n"
                + "ขั้นตอนต่อไปสามารถทำ Marketing Plan หรือ Financial Analysis ได้ครับ"
            )


        elif current_stage == "financial":
            append_assistant("กรุณากรอกข้อมูลในแบบฟอร์ม Financial Analysis ด้านล่างครับ")

        else:
            append_assistant("กรุณากด Start / Continue Plan เพื่อเริ่มต้นครับ")

        st.rerun()


# =========================================================
# Financial Analysis Section
# =========================================================

def growth_list_to_string(growth_list, default_text):
    if not growth_list:
        return default_text
    try:
        return "; ".join([f"{start}-{end}:{rate}" for start, end, rate in growth_list])
    except Exception:
        return default_text


def parse_growth_input(input_str):
    try:
        segments = input_str.split(";")
        parsed = []
        for seg in segments:
            if not seg.strip():
                continue
            yr_part, gr_part = seg.split(":")
            start, end = map(int, yr_part.strip().split("-"))
            rate = float(gr_part.strip())
            parsed.append((start, end, rate))
        return parsed
    except Exception as e:
        st.error(f"Invalid format: {e}")
        return None


if st.session_state.stage == "financial":

    step = st.session_state.financial_step
    fin = st.session_state.financial_inputs

    st.markdown(f"### 💰 Financial Analysis (Input / Revise) - Step {step}")
    
    if st.session_state.get("financial_mode") == "revise" and step == 1:
        st.info(
            "ระบบได้เปิดข้อมูล Financial Analysis เดิมขึ้นมาแล้ว "
            "ท่านสามารถแก้ไขเฉพาะรายการที่ต้องการ แล้วกด Submit เพื่อคำนวณใหม่ได้ครับ"
        )
    else:
        st.info(get_financial_step_prompt(step))

    # =========================
    # Step 3: Discount Rate
    # ต้องแยกออกจาก form ใหญ่
    # =========================

    if step == 3:
        old_approach = int(fin.get("discount_approach", 1))

        approach = st.radio(
            "Choose Discount Rate Approach",
            ["Direct Rate", "CAPM/WACC"],
            index=0 if old_approach == 1 else 1,
            key="discount_approach_radio"
        )

        with st.form(key="fin_step_3_form"):  

            if approach == "Direct Rate":
                rate = st.number_input(
                    "Discount Rate (0.1 = 10%)",
                    min_value=0.0,
                    max_value=1.0,
                    value=float(fin.get("discount_rate", 0.0)),
                    step=0.001,
                    format="%.3f"
                )

                submitted = st.form_submit_button("Submit Step 3 / Next")

                if submitted:
                    st.session_state.financial_inputs.update({
                        "discount_approach": 1,
                        "discount_rate": rate,
                    })
                    st.session_state.financial_step = 4
                    st.rerun()

            else:
                beta = st.number_input(
                    "Beta",
                    min_value=0.0,
                    value=float(fin.get("beta", 0.0)),
                    step=0.001,
                    format="%.3f"
                )

                risk_free = st.number_input(
                    "Risk-Free Rate",
                    min_value=0.0,
                    max_value=1.0,
                    value=float(fin.get("risk_free", 0.0)),
                    step=0.001,
                    format="%.3f"
                )

                premium = st.number_input(
                    "Market Premium",
                    min_value=0.0,
                    max_value=1.0,
                    value=float(fin.get("market_premium", 0.0)),
                    step=0.001,
                    format="%.3f"
                )

                debt_ratio = st.number_input(
                    "Debt Ratio",
                    min_value=0.0,
                    max_value=1.0,
                    value=float(fin.get("debt_ratio", 0.0)),
                    step=0.001,
                    format="%.3f"
                )

                cost_of_debt = st.number_input(
                    "Cost of Debt",
                    min_value=0.0,
                    max_value=1.0,
                    value=float(fin.get("cost_of_debt", 0.0)),
                    step=0.001,
                    format="%.3f"
                )
                tax_rate = float(fin.get("tax_rate", 0.0))
                cost_of_equity = risk_free + beta * premium

                calculated_discount_rate = (
                    (1 - debt_ratio) * cost_of_equity
                    + debt_ratio * (1 - tax_rate) * cost_of_debt
                )
                st.info(
                    f"Cost of Equity = {cost_of_equity:.3f} "
                    f"หรือ {cost_of_equity * 100:.2f}%\n\n"
                    f"WACC / Discount Rate = {calculated_discount_rate:.3f} "
                    f"หรือ {calculated_discount_rate * 100:.2f}%"
                )

                submitted = st.form_submit_button("Submit Step 3 / Next")

                if submitted:
                    st.session_state.financial_inputs.update({
                        "discount_approach": 2,
                        "beta": beta,
                        "risk_free": risk_free,
                        "market_premium": premium,
                        "debt_ratio": debt_ratio,
                        "cost_of_debt": cost_of_debt,
                        "discount_rate": calculated_discount_rate,
                    })
                    st.session_state.financial_step = 4
                    st.rerun()
    
    
    
    

    else:
        with st.form(key=f"fin_step_{step}"):

            if step == 1:
                col1, col2 = st.columns(2)

                with col1:
                    initial_investment = st.number_input(
                        "Initial Investment",
                        min_value=0.0,
                        value=float(fin.get("initial_investment", 0.0))
                    )
                    salvage = st.number_input(
                        "Salvage Value",
                        min_value=0.0,
                        value=float(fin.get("salvage_value", 0.0))
                    )
                    tax_credit = st.number_input(
                        "Tax Credit (0.1 = 10%)",
                        min_value=0.0,
                        max_value=1.0,
                        value=float(fin.get("tax_credit", 0.0))
                    )

                with col2:
                    lifetime = st.number_input(
                        "Lifetime (Years)",
                        min_value=1,
                        step=1,
                        value=int(fin.get("lifetime", 1))
                    )
                    depr_method = st.selectbox(
                        "Depreciation Method",
                        [1, 2],
                        index=0 if int(fin.get("depr_method", 1)) == 1 else 1,
                        format_func=lambda x: "Straight Line" if x == 1 else "DDB",
                    )

                submitted = st.form_submit_button("Submit Step 1 / Next")

                if submitted:
                    st.session_state.financial_inputs.update({
                        "initial_investment": initial_investment,
                        "salvage_value": salvage,
                        "tax_credit": tax_credit,
                        "lifetime": int(lifetime),
                        "depr_method": depr_method,
                    })
                    st.session_state.financial_step = 2
                    st.rerun()

            elif step == 2:
                cogs_items = fin.get("cogs_items", {})
                opex_items = fin.get("opex_items", {})

                revenue = st.number_input(
                    "Revenue Year 1",
                    min_value=0.0,
                    value=float(fin.get("revenue_year1", 0.0))
                )
                mat = st.number_input(
                    "COGS - Materials",
                    min_value=0.0,
                    value=float(cogs_items.get("Materials", 0.0))
                )
                labor = st.number_input(
                    "COGS - Direct Labor",
                    min_value=0.0,
                    value=float(cogs_items.get("Direct Labor", 0.0))
                )
                rent = st.number_input(
                    "Opex - Rent",
                    min_value=0.0,
                    value=float(opex_items.get("Rent", 0.0))
                )
                sal = st.number_input(
                    "Opex - Salaries",
                    min_value=0.0,
                    value=float(opex_items.get("Salaries", 0.0))
                )
                mkt = st.number_input(
                    "Opex - Marketing",
                    min_value=0.0,
                    value=float(opex_items.get("Marketing", 0.0))
                )
                supplies = st.number_input(
                    "Opex - Office Supplies",
                    min_value=0.0,
                    value=float(opex_items.get("Office Supplies", 0.0))
                )
                util = st.number_input(
                    "Opex - Utilities",
                    min_value=0.0,
                    value=float(opex_items.get("Utilities", 0.0))
                )
                tax = st.number_input(
                    "Tax Rate (40% = 0.4)",
                    min_value=0.0,
                    max_value=1.0,
                    value=float(fin.get("tax_rate", 0.0))
                )

                submitted = st.form_submit_button("Submit Step 2 / Next")

                if submitted:
                    st.session_state.financial_inputs.update({
                        "revenue_year1": revenue,
                        "cogs_items": {
                            "Materials": mat,
                            "Direct Labor": labor,
                        },
                        "opex_items": {
                            "Rent": rent,
                            "Salaries": sal,
                            "Marketing": mkt,
                            "Office Supplies": supplies,
                            "Utilities": util,
                        },
                        "tax_rate": tax,
                    })
                    st.session_state.financial_step = 3
                    st.rerun()

        
            elif step == 4:
                initial_wc = st.number_input(
                    "Initial Working Capital",
                    min_value=0.0,
                    value=float(fin.get("initial_wc", 0.0))
                )
                wc_percent = st.number_input(
                    "% of Revenue to WC (0.25 = 25%)",
                    min_value=0.0,
                    max_value=1.0,
                    value=float(fin.get("wc_percent", 0.0))
                )
                wc_salvage = st.number_input(
                    "% WC Recovered (1.0 = 100%)",
                    min_value=0.0,
                    max_value=1.0,
                    value=float(fin.get("wc_salvage", 1.0))
                )

                submitted = st.form_submit_button("Submit Step 4 / Next")

                if submitted:
                    st.session_state.financial_inputs.update({
                        "initial_wc": initial_wc,
                        "wc_percent": wc_percent,
                        "wc_salvage": wc_salvage,
                    })
                    st.session_state.financial_step = 5
                    st.rerun()

            elif step == 5:
                st.caption(
                    "ใส่อัตราการเติบโตในรูปแบบ เช่น "
                    "`1-5:0.05; 6-8:0.03; 9-10:0.02`"
                )

                revenue_growth_str = st.text_input(
                    "Revenue Growth Ranges",
                    value=growth_list_to_string(
                        fin.get("growth_revenue", []),
                        "1-5:0.05; 6-8:0.03; 9-10:0.02"
                    ),
                )
                cogs_growth_str = st.text_input(
                    "COGS Growth Ranges",
                    value=growth_list_to_string(
                        fin.get("growth_cogs", []),
                        "1-4:0.05; 5-6:0.04; 7-8:0.03; 9-10:0.02"
                    ),
                )
                opex_growth_str = st.text_input(
                    "Operating Expense Growth Ranges",
                    value=growth_list_to_string(
                        fin.get("growth_opex", []),
                        "1-4:0.05; 5-6:0.04; 7-8:0.03; 9-10:0.02"
                    ),
                )

                submitted = st.form_submit_button("Submit Step 5 / Recalculate Financial Analysis")

                if submitted:
                    growth_revenue = parse_growth_input(revenue_growth_str)
                    growth_cogs = parse_growth_input(cogs_growth_str)
                    growth_opex = parse_growth_input(opex_growth_str)

                    if growth_revenue and growth_cogs and growth_opex:
                        st.session_state.financial_inputs.update({
                            "growth_revenue": growth_revenue,
                            "growth_cogs": growth_cogs,
                            "growth_opex": growth_opex,
                        })

                        filepath = calculate_financials(st.session_state.financial_inputs)
                        st.session_state.financial_file = filepath
                        st.session_state.stage = "financial_done"
                        st.session_state.financial_step = 0
                        st.session_state.financial_completed = True
                        st.session_state.financial_mode = "revise"

                        append_assistant(
                            "Financial Analysis เสร็จเรียบร้อยแล้ว สามารถดาวน์โหลดไฟล์ Excel ได้ด้านล่างครับ หากต้องการปรับสมมติฐาน ให้กด Financial Analysis (Input / Revise) อีกครั้งครับ"
                        )

                        st.rerun()

# =========================================================
# Financial File Download
# =========================================================
if st.session_state.financial_file:
    with open(st.session_state.financial_file, "rb") as f:
        st.download_button(
            "📥 Download Financial Excel",
            f,
            file_name=st.session_state.financial_file,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )


# =========================================================
# Full Conversation
# =========================================================
if st.checkbox("📜 Show Full Conversation"):
    for msg in st.session_state.chat_log:
        st.markdown(f"**{msg['role'].capitalize()}:** {msg['content']}")
