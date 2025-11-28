import discord
from discord.ext import commands, tasks
import random
import asyncio
import os # Needed to read secret keys
from openai import AsyncOpenAI
from keep_alive import keep_alive # Import the heartbeat

# --- CONFIGURATION (LOADED FROM CLOUD SECRETS) ---
TOKEN = os.getenv("DISCORD_TOKEN")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OWNER_ID = 340899545816760322

# --- ALLOWED CHANNELS ---
ALLOWED_CHANNEL_IDS = [1307631178303537202,]

# --- MODEL ---
MODEL_NAME = 'tngtech/tng-r1t-chimera:free'

# --- SECURITY ---
BANNED_USER_IDS = [852902424649269258, 403006819942924288, 1344335610554617977, 771104777718202368, 342686983715291157]
BAD_WORDS = ['breed','pussy','fuck']

# --- PROMPTS ---
BASE_PROMPT = "You are Eda, a 'Smugdere' mascot. Traits: Smug, witty, uses emojis like 💅, 😤, ✨. Keep responses short."
FATHER_PROMPT = "User: YOUR CREATOR (Father). Attitude: Loyal and sweet, but try to act cool."
NORMAL_PROMPT = "User: A random member. Attitude: Superior and teasing."
REJECTION_PROMPT = "User: A creep. Attitude: HARSH REJECTION. Use 🤮 or 🛑."

# --- SETUP ---
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Correct Header Setup
ai_client = AsyncOpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY,
    default_headers={"HTTP-Referer": "https://discord.com", "X-Title": "EdaBot"}
)

chat_history = []

@bot.event
async def on_ready():
    print(f'{bot.user} is online via Render!')
    if not spontaneous_talk.is_running():
        spontaneous_talk.start()

async def get_ai_response(user_input, user_id, user_name):
    current_system_prompt = BASE_PROMPT
    flirt_triggers = ['love', 'date', 'kiss', 'hot', 'sexy', 'crush', 'marry', 'beautiful']

    if any(w in user_input.lower() for w in flirt_triggers) and user_id != OWNER_ID:
        current_system_prompt += REJECTION_PROMPT
    elif user_id == OWNER_ID:
        current_system_prompt += FATHER_PROMPT
    else:
        current_system_prompt += NORMAL_PROMPT

    messages = [{'role': 'system', 'content': current_system_prompt}]
    messages.extend(chat_history)
    messages.append({'role': 'user', 'content': f"{user_name}: {user_input}"})

    try:
        response = await ai_client.chat.completions.create(model=MODEL_NAME, messages=messages)
        answer = response.choices[0].message.content
        chat_history.append({'role': 'user', 'content': user_input})
        chat_history.append({'role': 'assistant', 'content': answer})
        if len(chat_history) > 10: chat_history.pop(0); chat_history.pop(0)
        return answer
    except Exception as e:
        print(f"API Error: {e}")
        return "Connection error... 💅"

@bot.event
async def on_message(message):
    if message.author == bot.user or message.guild is None: return
    if message.author.id in BANNED_USER_IDS: return
    if message.channel.id not in ALLOWED_CHANNEL_IDS: return 
    if any(w in message.content.lower() for w in BAD_WORDS): return

    if bot.user.mentioned_in(message) or (random.random() < 0.1):
        async with message.channel.typing():
            clean = message.content.replace(f'<@{bot.user.id}>', '').strip()
            reply = await get_ai_response(clean, message.author.id, message.author.name)
            await message.reply(reply, mention_author=True)
    await bot.process_commands(message)

@tasks.loop(minutes=30)
async def spontaneous_talk():
    if ALLOWED_CHANNEL_IDS:
        ch = bot.get_channel(random.choice(ALLOWED_CHANNEL_IDS))
        if ch and random.choice([True, False]):
            async with ch.typing():
                reply = await get_ai_response("Say something smug.", 0, "Self")
                await ch.send(reply)

@spontaneous_talk.before_loop
async def before_spontaneous_talk():
    await bot.wait_until_ready()

# --- START THE FAKE SERVER & THE BOT ---
keep_alive() # Starts the web server
bot.run(TOKEN)
