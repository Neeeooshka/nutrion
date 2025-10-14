# handlers/profile.py
from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from backend.llm_profile import save_profile, get_profile

profile_router = Router()

# --- FSM состояния анкеты ---
class ProfileForm(StatesGroup):
    gender = State()
    age = State()
    weight = State()
    goal = State()
    diet = State()


# --- FSM начало анкеты ---
async def start_profile_flow(msg: types.Message, state: FSMContext):
    await state.clear()
    text = (
        "👋 Привет! Я Нутрион — твой AI-ассистент по питанию и тренировкам.\n\n"
        "Давай познакомимся поближе — ответь на несколько вопросов, чтобы я мог подобрать рекомендации специально для тебя 💪\n\n"
    )
    await msg.answer(text, parse_mode="Markdown")
    await msg.answer("🔹 Укажи свой пол (м/ж):")
    await state.set_state(ProfileForm.gender)
    
# --- Команда /start ---
@profile_router.message(Command("start"))
async def cmd_start(msg: types.Message, state: FSMContext):
    await start_profile_flow(msg, state)

# --- FSM шаги анкеты ---
@profile_router.message(ProfileForm.gender)
async def process_gender(msg: types.Message, state: FSMContext):
    gender = msg.text.strip().lower()
    if gender not in ["м", "ж"]:
        await msg.answer("Пожалуйста, введи **м** или **ж** 🙂", parse_mode="Markdown")
        return
    await state.update_data(gender=gender)
    await msg.answer("📅 Укажи свой возраст (в годах):")
    await state.set_state(ProfileForm.age)

@profile_router.message(ProfileForm.age)
async def process_age(msg: types.Message, state: FSMContext):
    if not msg.text.isdigit() or int(msg.text) < 10 or int(msg.text) > 100:
        await msg.answer("Введите корректный возраст (от 10 до 100).")
        return
    await state.update_data(age=int(msg.text))
    await msg.answer("⚖️ Укажи свой вес (в кг):")
    await state.set_state(ProfileForm.weight)

@profile_router.message(ProfileForm.weight)
async def process_weight(msg: types.Message, state: FSMContext):
    try:
        weight = float(msg.text.replace(",", "."))
    except ValueError:
        await msg.answer("Введите число, например `72.5` кг.", parse_mode="Markdown")
        return
    await state.update_data(weight=weight)
    await msg.answer("🎯 Какая у тебя цель?\n\n1️⃣ Похудеть\n2️⃣ Поддерживать форму\n3️⃣ Набрать массу")
    await state.set_state(ProfileForm.goal)

@profile_router.message(ProfileForm.goal)
async def process_goal(msg: types.Message, state: FSMContext):
    goals = {"1": "Похудеть", "2": "Поддерживать форму", "3": "Набрать массу"}
    goal = goals.get(msg.text.strip()) or msg.text.strip().capitalize()
    await state.update_data(goal=goal)
    await msg.answer("🥗 Какое у тебя питание?\nНапример: 'Всеядный', 'Вегетарианец', 'Кето' и т.д.")
    await state.set_state(ProfileForm.diet)

@profile_router.message(ProfileForm.diet)
async def process_diet(msg: types.Message, state: FSMContext):
    await state.update_data(diet=msg.text.strip())
    data = await state.get_data()
    chat_id = msg.chat.id
    user_id = msg.from_user.id

    # Сохраняем в БД
    await save_profile(chat_id, user_id, data)
    await state.clear()

    summary = (
        f"✅ Отлично! Я запомнил твой профиль:\n\n"
        f"👤 Пол: {data['gender'].upper()}\n"
        f"📅 Возраст: {data['age']} лет\n"
        f"⚖️ Вес: {data['weight']} кг\n"
        f"🎯 Цель: {data['goal']}\n"
        f"🥗 Питание: {data['diet']}\n\n"
        "Хочешь, я помогу рассчитать калорийность и составлю меню\n"
        "или распишу план тренировок для мощной бицухи или ягодицы? 🍑💪\n"
    )
    await msg.answer(summary)

# --- Команда /profile ---
@profile_router.message(Command("profile"))
async def cmd_profile(msg: types.Message):
    chat_id = msg.chat.id
    user_id = msg.from_user.id
    data = await get_profile(chat_id, user_id)
    if not data:
        await msg.answer("Профиль пока не заполнен. Напиши /start, чтобы пройти анкету.")
        return

    profile_text = (
        f"👤 *Твой профиль:*\n\n"
        f"Пол: {data['gender'].upper()}\n"
        f"Возраст: {data['age']}\n"
        f"Вес: {data['weight']} кг\n"
        f"Цель: {data['goal']}\n"
        f"Питание: {data['diet']}\n\n"
        "Чтобы изменить данные, просто напиши /start и пройди анкету заново 💡"
    )
    await msg.answer(profile_text, parse_mode="Markdown")

# --- Команда /help ---
@profile_router.message(Command("help"))
async def cmd_help(msg: types.Message):
    text = (
        "📘 *Что я умею:*\n\n"
        "🤖 Давать персональные рекомендации по питанию и тренировкам\n"
        "🍎 Помогать рассчитать КБЖУ и составить меню\n"
        "📸 (в будущем) Распознавать еду по фото\n"
        "🧠 Запоминать историю диалога и твои цели\n\n"
        "📍 Основные команды:\n"
        "/start — начать или обновить анкету\n"
        "/profile — посмотреть свои данные\n"
        "/help — показать это меню\n"
    )
    await msg.answer(text, parse_mode="Markdown")
