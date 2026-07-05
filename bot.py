import asyncio
import os
import logging
from aiogram import Bot, Dispatcher, Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message, FSInputFile
import yt_dlp

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.environ.get("BOT_TOKEN")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
router = Router()
dp.include_router(router)

DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

def download_video_sync(url: str) -> str:
    ydl_opts = {
        'format': 'bestvideo[height<=720]+bestaudio/best[height<=720]/best',
        'outtmpl': f'{DOWNLOAD_DIR}/%(id)s.%(ext)s',
        'merge_output_format': 'mp4',
        'noplaylist': True,
        'quiet': True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        return ydl.prepare_filename(info)

@router.message(CommandStart())
async def cmd_start(message: Message):
    text = (
        "Привет! 👋\n"
        "Я бот для скачивания видео.\n"
        "Просто отправь ссылку на видео из Instagram, TikTok или YouTube! 🎬"
    )
    await message.answer(text)

@router.message(F.text.startswith('http'))
async def handle_link(message: Message):
    url = message.text.strip()
    
    try:
        loop = asyncio.get_running_loop()
        file_path = await loop.run_in_executor(None, download_video_sync, url)
        
        if not os.path.exists(file_path):
            raise FileNotFoundError("Файл не был скачан.")

        file_size = os.path.getsize(file_path)
        if file_size > 50 * 1024 * 1024:
            await message.answer("⚠️ Видео больше 50 МБ — Telegram не пропустит.")
            os.remove(file_path)
            return

        video_file = FSInputFile(file_path)
        await message.answer_video(video=video_file, caption="🎥 Готово!")
        
    except Exception as e:
        error_msg = str(e)
        await message.answer(f"❌ Ошибка: {error_msg[:200]}")
    finally:
        if 'file_path' in locals() and os.path.exists(file_path):
            os.remove(file_path)

@router.message()
async def handle_invalid(message: Message):
    await message.answer("Отправь ссылку на видео (начинается с http:// или https://)")

async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
