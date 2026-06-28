import asyncio
import aiohttp
from modules.maps_search import MapsSearch

async def test():
    config = {"timeout_seconds": 30}
    ms = MapsSearch(config)
    
    # Fake session not needed for maps_search itself, it just takes it as argument
    # We will search "Plastic Surgeon" in "Atlanta"
    print("Testing Maps Search...")
    businesses = await ms.search("Plastic Surgeon", "Atlanta", None)
    
    print(f"Found {len(businesses)} businesses.")
    for b in businesses[:10]:
        print(f"Name: {b['name']} | Website: {b['website']}")

if __name__ == "__main__":
    asyncio.run(test())
