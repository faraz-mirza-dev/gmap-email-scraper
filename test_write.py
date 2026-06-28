import asyncio
from modules.csv_writer import CSVWriter

async def main():
    writer = CSVWriter({})
    await writer.init_files()
    await writer.write_row("businesses_found", {
        "keyword": "test",
        "city": "test",
        "business_name": "test",
        "website": "test.com",
        "address": "",
        "phone": ""
    })
    print("Done")

asyncio.run(main())
