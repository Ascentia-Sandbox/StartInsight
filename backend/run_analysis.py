"""Script to run AI analysis on raw signals."""
import asyncio
import logging
import os
from pathlib import Path

from dotenv import load_dotenv

# Load environment from .env file
env_path = Path(__file__).parent / ".env"
load_dotenv(env_path)

# Verify API key is loaded
print(f'GOOGLE_API_KEY present: {bool(os.environ.get("GOOGLE_API_KEY"))}')

from app.worker import analyze_signals_task

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

async def run_analysis():
    ctx = {}
    print('')
    print('=== Running AI Analysis on Raw Signals with Gemini ===')
    result = await analyze_signals_task(ctx)
    print(f'Result: {result}')

if __name__ == "__main__":
    asyncio.run(run_analysis())
