import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from langchain_community.utilities import SQLDatabase
from langchain_openai import ChatOpenAI
from langchain_community.agent_toolkits import create_sql_agent
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.tools import Tool
from langgraph.prebuilt import create_react_agent

load_dotenv()

# ── System prompt ──────────────────────────────────────────────
def load_system_prompt(file_path: str) -> str:
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    return (
        "أنت مساعد ذكي للصيدلية. يمكنك الدردشة العادية والإجابة على الأسئلة الشخصية. "
        "لديك أداة للوصول لقاعدة البيانات — استخدمها فقط عندما يحتاج السؤال بيانات أو أرقام. "
        "راجع الـ chat_history دائماً قبل الإجابة."
    )

system_instruction = load_system_prompt("system_prompt.txt")

# ── Per-user memory ─────────────────────────────────────────────
user_memories: dict[int, ChatMessageHistory] = {}

def get_memory(user_id: int) -> ChatMessageHistory:
    if user_id not in user_memories:
        user_memories[user_id] = ChatMessageHistory()
    return user_memories[user_id]

# ── LLM ────────────────────────────────────────────────────────
llm = ChatOpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENAI_API_KEY"),
    model="openai/gpt-oss-120b:free",
    temperature=0.5,
)

# ── SQL sub-agent as Tool ───────────────────────────────────────
db = SQLDatabase.from_uri(os.getenv("DATABASE_URL"), schema="pharmacy")

sql_agent_executor = create_sql_agent(
    llm,
    db=db,
    agent_type="openai-tools",
    verbose=True,
)

def run_sql_query(question: str) -> str:
    """يستعلم من قاعدة بيانات الصيدلية ويرجع النتيجة."""
    try:
        result = sql_agent_executor.invoke({"input": question})
        return result.get("output", "لم أجد نتيجة من قاعدة البيانات.")
    except Exception as e:
        return f"خطأ في الاستعلام: {e}"

pharmacy_db_tool = Tool(
    name="pharmacy_database",
    func=run_sql_query,
    description=(
        "استخدم هذه الأداة فقط عندما يسأل المستخدم عن بيانات من قاعدة البيانات: "
        "مثل الأدوية، الأسعار، المخزون، الوصفات، الفواتير، المبيعات، أو أي أرقام و العملة بالجنية . "
        "لا تستخدمها للدردشة العادية أو الأسئلة الشخصية."
        "مثال: 'كم سعر دواء X؟' أو 'ما هو المخزون الحالي لدواء Y؟'"
        "تأكد أن تسأل المستخدم عن التفاصيل اللازمة إذا كان السؤال غير واضح، مثل اسم الدواء أو الفترة الزمنية."
        "تذكر أن تراجع الـ chat_history دائماً قبل استخدام الأداة، فقد تجد الإجابة هناك بدون الحاجة لقاعدة البيانات."
        "كن حذرًا في صياغة استعلامات SQL، وتأكد من أن تكون آمنة وخالية من أي محاولات حقن SQL."
        "إذا لم تكن متأكدًا من صياغة الاستعلام، اسأل المستخدم عن مزيد من التفاصيل بدلاً من التخمين."
        "لو سال علي اسم دواء و انت مش لاقية شوف اقرب دواء موجود عندك شبهه في الاسم و اسأله اذا هو يقصده ولا لأ."
    ),
)

# ── Main agent (LangGraph ReAct) ────────────────────────────────
agent_executor = create_react_agent(
    llm,
    tools=[pharmacy_db_tool],
    prompt=SystemMessage(content=system_instruction),
)

# ── Telegram handlers ───────────────────────────────────────────
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "أهلاً بك! أنا مساعدك الذكي في الصيدلية، كيف يمكنني مساعدتك اليوم؟"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id  = update.message.from_user.id
    user_question = update.message.text
    history  = get_memory(user_id)

    status_msg = await update.message.reply_text("جاري التفكير... ⏳")

    try:
        messages_input = history.messages + [HumanMessage(content=user_question)]
        response = agent_executor.invoke({"messages": messages_input})

        final_answer = response["messages"][-1].content

        history.add_user_message(user_question)
        history.add_ai_message(final_answer)

        await status_msg.edit_text(final_answer)

    except Exception as e:
        await status_msg.edit_text(f"عذراً، واجهت مشكلة: {e}")

if __name__ == "__main__":
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not bot_token:
        raise ValueError("TELEGRAM_BOT_TOKEN مش موجود في الـ .env")

    app = ApplicationBuilder().token(bot_token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))

    print("✅ البوت شغال — LangGraph ReAct Agent | SQL كـ Tool اختياري")
    app.run_polling()