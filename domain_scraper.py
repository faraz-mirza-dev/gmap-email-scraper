import logging
logging.getLogger("asyncio").setLevel(logging.CRITICAL)
logging.getLogger("aiohttp").setLevel(logging.CRITICAL)
import asyncio
from scraper import ScraperOrchestrator

async def main():
    orchestrator = ScraperOrchestrator()
    await orchestrator.run_scraper(skip_phase_2=True)

if __name__ == "__main__":
    asyncio.run(main())
