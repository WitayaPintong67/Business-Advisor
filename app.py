
import streamlit as st

import openai
import json

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
        # waiting_suggestion_approval
        # waiting_replacement_input
        # waiting_edit_decision
        # waiting_edit_input
        st.session_state.swot_substage = None

    if "swot_pending_suggestion" not in st.session_state:
        st.session_state.swot_pending_suggestion = ""

    if "financial_step" not in st.session_state:
        st.session_state.financial_step = 0

    if "financial_inputs" not in st.session_state:
        st.session_state.financial_inputs = {}

    if "financial_file" not in st.session_state:
        st.session_state.financial_file = None

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


def is_yes(text):
    t = normalize_text(text)
    yes_words = [
        "ใช่",
        "ใช้",
        "ตกลง",
        "โอเค",
        "ok",
        "yes",
        "y",
        "เอา",
        "ยืนยัน",
        "ตามนี้",
        "ใช้ตามนี้",
    ]
    return any(t == w or t.startswith(w) for w in yes_words)


def is_no(text):
    t = normalize_text(text)
    no_words = [
        "ไม่",
        "ไม่ใช่",
        "ไม่เอา",
        "no",
        "n",
        "ขอแก้",
        "แก้ไข",
        "เปลี่ยน",
    ]
    return any(t == w or t.startswith(w) for w in no_words)


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
        "suggest",
        "example",
        "recommend",
    ]
    return any(k in t for k in keywords)


def get_swot_intro_prompt(item_key):
    item = SWOT_ITEMS[item_key]
    return (
        f"กรุณาระบุ **{item['label_th']} ({item['label_en']})** ของธุรกิจนี้\n\n"
        f"ตัวอย่างประเด็นที่อาจพิจารณา ได้แก่ {item['examples']}\n\n"
        f"ถ้าคุณมีข้อมูลอยู่แล้ว สามารถพิมพ์ {item['label_th']} เป็นข้อ ๆ ได้เลยครับ\n\n"
        f"แต่ถ้าต้องการให้ Chatbot ช่วยแนะนำ {item['label_th']} จากข้อมูลธุรกิจเบื้องต้น "
        f"ให้พิมพ์ว่า **ช่วยแนะนำ{item['label_th']}ให้หน่อย** ได้เลยครับ"
    )


def get_next_swot_item(item_key):
    return SWOT_ITEMS[item_key]["next"]


def generate_swot_suggestion(item_key):
    item = SWOT_ITEMS[item_key]
    business_info = st.session_state.plan_data.get("business_info", "")
    strengths = st.session_state.plan_data.get("strengths", "")
    weaknesses = st.session_state.plan_data.get("weaknesses", "")
    opportunities = st.session_state.plan_data.get("opportunities", "")

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

โปรดช่วยเสนอ {item['label_th']} ({item['label_en']}) สำหรับธุรกิจนี้ จำนวน 5-8 ข้อ

เงื่อนไข:
- ตอบเป็นภาษาไทย
- เขียนเป็นรายการ numbered list
- ให้เหมาะกับการนำไปใช้ใน SWOT Analysis
- อย่าเขียนยาวเกินไป
- อย่าใส่ Vision, Mission, Objectives หรือ Strategy ในคำตอบนี้
"""

    return ask_gpt(prompt, use_chat_history=False)


def save_confirmed_swot_item(item_key, content):
    st.session_state.plan_data[item_key] = content

    item = SWOT_ITEMS[item_key]
    st.session_state.chat_log.append({
        "role": "assistant",
        "content": f"✅ บันทึก {item['label_th']} ({item['label_en']}) ที่ผู้ใช้ยืนยันแล้ว:\n\n{content}"
    })


def ask_edit_decision(item_key):
    item = SWOT_ITEMS[item_key]
    return (
        f"ผมได้บันทึก **{item['label_th']} ({item['label_en']})** แล้วครับ\n\n"
        f"คุณต้องการแก้ไขหรือเพิ่มเติม {item['label_th']} อีกหรือไม่?\n\n"
        f"กรุณาตอบสั้น ๆ ว่า **แก้ไข** หรือ **ไม่แก้ไข**\n\n"
        f"- ถ้าตอบ **แก้ไข** ผมจะให้คุณพิมพ์ {item['label_th']} ฉบับใหม่\n"
        f"- ถ้าตอบ **ไม่แก้ไข** เราจะไปขั้นตอนถัดไปครับ"
    )


def move_to_next_swot_item_or_finish(current_item):
    next_item = get_next_swot_item(current_item)

    if next_item:
        st.session_state.swot_current_item = next_item
        st.session_state.swot_substage = "input_or_request_suggestion"
        return (
            f"ขั้นต่อไปคือการวิเคราะห์ **{SWOT_ITEMS[next_item]['label_th']} "
            f"({SWOT_ITEMS[next_item]['label_en']})**\n\n"
            + get_swot_intro_prompt(next_item)
        )

    st.session_state.stage = "vision_ready"
    st.session_state.swot_current_item = None
    st.session_state.swot_substage = None

    return generate_swot_summary()


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
        return get_swot_intro_prompt("strengths")

    item = SWOT_ITEMS[item_key]

    # 1) User either enters own SWOT item or asks GPT for suggestion
    if substage == "input_or_request_suggestion":
        if is_requesting_example(message):
            suggestion = generate_swot_suggestion(item_key)
            st.session_state.swot_pending_suggestion = suggestion
            st.session_state.swot_substage = "waiting_suggestion_approval"

            return (
                f"ผมขอเสนอ **{item['label_th']} ({item['label_en']})** เบื้องต้นดังนี้ครับ\n\n"
                f"{suggestion}\n\n"
                f"คุณต้องการใช้ {item['label_th']} ตามนี้หรือไม่?\n\n"
                f"กรุณาตอบสั้น ๆ ว่า **ใช่** หรือ **ไม่ใช่**"
            )

        save_confirmed_swot_item(item_key, message)
        st.session_state.swot_substage = "waiting_edit_decision"
        return ask_edit_decision(item_key)

    # 2) User approves or rejects GPT suggestion
    if substage == "waiting_suggestion_approval":
        if is_yes(message):
            confirmed = st.session_state.swot_pending_suggestion
            save_confirmed_swot_item(item_key, confirmed)
            st.session_state.swot_pending_suggestion = ""
            st.session_state.swot_substage = "waiting_edit_decision"
            return ask_edit_decision(item_key)

        if is_no(message):
            st.session_state.swot_substage = "waiting_replacement_input"
            return (
                f"ได้ครับ กรุณาระบุ **{item['label_th']} ({item['label_en']})** "
                f"ที่คุณเห็นว่าเหมาะสมเป็นข้อ ๆ ได้เลยครับ"
            )

        return (
            "กรุณาตอบสั้น ๆ ว่า **ใช่** หรือ **ไม่ใช่** ครับ\n\n"
            f"ถ้าตอบ **ใช่** ผมจะบันทึก {item['label_th']} ที่เสนอไว้\n"
            f"ถ้าตอบ **ไม่ใช่** คุณสามารถระบุ {item['label_th']} ใหม่เองได้ครับ"
        )

    # 3) User rejected suggestion and provides replacement input
    if substage == "waiting_replacement_input":
        save_confirmed_swot_item(item_key, message)
        st.session_state.swot_substage = "waiting_edit_decision"
        return ask_edit_decision(item_key)

    # 4) Ask whether user wants to edit the confirmed SWOT item
    if substage == "waiting_edit_decision":
        if is_yes(message) or "แก้" in normalize_text(message) or "เพิ่มเติม" in normalize_text(message):
            st.session_state.swot_substage = "waiting_edit_input"
            return (
                f"ได้ครับ กรุณาพิมพ์ **{item['label_th']} ({item['label_en']}) ฉบับปรับปรุงใหม่ทั้งหมด**\n\n"
                "ผมจะใช้ข้อความใหม่นี้แทนข้อความเดิมที่บันทึกไว้ครับ"
            )

        if is_no(message) or "ไม่แก้" in normalize_text(message) or "ไม่เพิ่มเติม" in normalize_text(message):
            return move_to_next_swot_item_or_finish(item_key)

        return (
            f"กรุณาตอบว่า **แก้ไข** หรือ **ไม่แก้ไข** ครับ\n\n"
            f"ถ้าต้องการแก้ไข/เพิ่มเติม {item['label_th']} ให้ตอบว่า **แก้ไข**\n"
            f"ถ้าพอใจแล้วและต้องการไปขั้นตอนถัดไป ให้ตอบว่า **ไม่แก้ไข**"
        )

    # 5) User provides revised final version
    if substage == "waiting_edit_input":
        st.session_state.plan_data[item_key] = message
        append_assistant(
            f"✅ ผมได้อัปเดต **{item['label_th']} ({item['label_en']})** เป็นฉบับใหม่แล้วครับ:\n\n{message}"
        )
        return move_to_next_swot_item_or_finish(item_key)

    return get_swot_intro_prompt(item_key)


# =========================================================
# Styling
# =========================================================
st.markdown("""
<style>
.block-container { padding-top: 1rem; }
.title-container {
    background-color: #cce0cc;
    padding: 35px;
    border-radius: 8px;
    margin-bottom: 25px;
}
.header-assistant {
    background-color: #dcefd8;
    padding: 10px;
    border-radius: 6px;
    font-weight: bold;
    font-size: 28px;
}
.header-user {
    background-color: #dbeaf4;
    padding: 10px;
    border-radius: 6px;
    font-weight: bold;
    font-size: 28px;
}
.chat-message {
    font-size: 22px;
    line-height: 1.6;
    padding: 8px 0;
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
            append_assistant(get_swot_intro_prompt(current_item))
        elif st.session_state.stage == "vision_ready":
            append_assistant(
                "ตอนนี้ SWOT Analysis เสร็จแล้วครับ\n\n"
                "ขั้นต่อไปคือการพัฒนา Vision, Mission และ Objectives "
                "จากข้อมูลธุรกิจและ SWOT ที่ได้ยืนยันไว้แล้ว"
            )
        st.rerun()

with cols[1]:
    if st.button("💰 Financial Analysis", use_container_width=True):
        st.session_state.stage = "financial"
        st.session_state.financial_step = 1
        st.rerun()

with cols[2]:
    if st.button("💾 Save Project", use_container_width=True):
        data = {
            "chat_log": st.session_state.chat_log,
            "stage": st.session_state.stage,
            "plan_data": st.session_state.plan_data,
            "swot_current_item": st.session_state.swot_current_item,
            "swot_substage": st.session_state.swot_substage,
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
        '<div class="header-assistant" style="text-align:center;">🧠 Assistant (System)</div>',
        unsafe_allow_html=True,
    )
    for msg in st.session_state.chat_log:
        if msg["role"] == "assistant":
            content_html = msg["content"].replace("\n", "<br>")
            st.markdown(
                f"<div class='chat-message'><strong>Assistant:</strong> {content_html}</div>",
                unsafe_allow_html=True,
            )

with col_you:
    st.markdown(
        '<div class="header-user" style="text-align:center;">👤 You (User Input)</div>',
        unsafe_allow_html=True,
    )
    for msg in st.session_state.chat_log:
        if msg["role"] == "user":
            content_html = msg["content"].replace("\n", "<br>")
            st.markdown(
                f"<div class='chat-message'><strong>You:</strong> {content_html}</div>",
                unsafe_allow_html=True,
            )


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

        elif current_stage == "vision_ready":
            append_assistant(
                "ตอนนี้ SWOT Analysis เสร็จแล้วครับ\n\n"
                "ขั้นต่อไปเราจะพัฒนา Vision, Mission และ Objectives "
                "จากข้อมูลธุรกิจและ SWOT ที่ได้วิเคราะห์ไว้"
            )

        elif current_stage == "financial":
            append_assistant("กรุณากรอกข้อมูลในแบบฟอร์ม Financial Analysis ด้านล่างครับ")

        else:
            append_assistant("กรุณากด Start / Continue Plan เพื่อเริ่มต้นครับ")

        # Clear input box after send
        #st.session_state.user_input = "" เดิมที่มีคำสั่งนี้
        st.rerun()


# =========================================================
# Financial Analysis Section
# =========================================================
if st.session_state.stage == "financial":

    step = st.session_state.financial_step

    st.markdown(f"### 💰 Financial Analysis - Step {step}")
    st.info(get_financial_step_prompt(step))

    with st.form(key=f"fin_step_{step}"):

        if step == 1:
            col1, col2 = st.columns(2)

            with col1:
                initial_investment = st.number_input("Initial Investment", min_value=0.0)
                salvage = st.number_input("Salvage Value", min_value=0.0)
                tax_credit = st.number_input("Tax Credit (0.1 = 10%)", min_value=0.0, max_value=1.0)

            with col2:
                lifetime = st.number_input("Lifetime (Years)", min_value=1, step=1)
                depr_method = st.selectbox(
                    "Depreciation Method",
                    [1, 2],
                    format_func=lambda x: "Straight Line" if x == 1 else "DDB",
                )

            submitted = st.form_submit_button("Submit Step 1")

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
            revenue = st.number_input("Revenue Year 1", min_value=0.0)
            mat = st.number_input("COGS - Materials", min_value=0.0)
            labor = st.number_input("COGS - Direct Labor", min_value=0.0)
            rent = st.number_input("Opex - Rent", min_value=0.0)
            sal = st.number_input("Opex - Salaries", min_value=0.0)
            mkt = st.number_input("Opex - Marketing", min_value=0.0)
            supplies = st.number_input("Opex - Office Supplies", min_value=0.0)
            util = st.number_input("Opex - Utilities", min_value=0.0)
            tax = st.number_input("Tax Rate", min_value=0.0, max_value=1.0)

            submitted = st.form_submit_button("Submit Step 2")

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

        elif step == 3:
            approach = st.radio("Choose Discount Rate Approach", ["Direct Rate", "CAPM/WACC"])

            if approach == "Direct Rate":
                rate = st.number_input("Discount Rate (0.1 = 10%)", min_value=0.0, max_value=1.0)
                submitted = st.form_submit_button("Submit Step 3")

                if submitted:
                    st.session_state.financial_inputs.update({
                        "discount_approach": 1,
                        "discount_rate": rate,
                    })
                    st.session_state.financial_step = 4
                    st.rerun()

            else:
                beta = st.number_input("Beta", min_value=0.0)
                risk_free = st.number_input("Risk-Free Rate", min_value=0.0, max_value=1.0)
                premium = st.number_input("Market Premium", min_value=0.0, max_value=1.0)
                debt_ratio = st.number_input("Debt Ratio", min_value=0.0, max_value=1.0)
                cost_of_debt = st.number_input("Cost of Debt", min_value=0.0, max_value=1.0)

                submitted = st.form_submit_button("Submit Step 3")

                if submitted:
                    st.session_state.financial_inputs.update({
                        "discount_approach": 2,
                        "beta": beta,
                        "risk_free": risk_free,
                        "market_premium": premium,
                        "debt_ratio": debt_ratio,
                        "cost_of_debt": cost_of_debt,
                    })
                    st.session_state.financial_step = 4
                    st.rerun()

        elif step == 4:
            initial_wc = st.number_input("Initial Working Capital", min_value=0.0)
            wc_percent = st.number_input("% of Revenue to WC (0.2 = 20%)", min_value=0.0, max_value=1.0)
            wc_salvage = st.number_input("% WC Recovered", min_value=0.0, max_value=1.0)

            submitted = st.form_submit_button("Submit Step 4")

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
                "`1-3:0.05; 4-6:0.10; 7-10:0.03`"
            )

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

            revenue_growth_str = st.text_input(
                "Revenue Growth Ranges",
                value="1-3:0.05; 4-6:0.10; 7-10:0.03",
            )
            cogs_growth_str = st.text_input(
                "COGS Growth Ranges",
                value="1-3:0.04; 4-6:0.07; 7-10:0.02",
            )
            opex_growth_str = st.text_input(
                "Operating Expense Growth Ranges",
                value="1-3:0.03; 4-6:0.05; 7-10:0.01",
            )

            submitted = st.form_submit_button("Submit Step 5")

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

                    append_assistant(
                        "Financial Analysis เสร็จเรียบร้อยแล้ว สามารถดาวน์โหลดไฟล์ Excel ได้ด้านล่างครับ"
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
