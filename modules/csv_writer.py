import csv
import aiofiles
import os
import asyncio
from typing import Dict, List, Any

class CSVWriter:
    def __init__(self, config: dict):
        self.config = config
        self.lock = asyncio.Lock()
        
        self.files = {
            "business_emails": {
                "path": config.get("output_files", {}).get("business_emails", "business_emails.csv"),
                "headers": ["keyword", "city", "business_name", "website", "primary_email", "all_emails", "mx_valid", "address", "phone", "scraped_at"]
            },
            "free_emails": {
                "path": config.get("output_files", {}).get("free_emails", "free_email_providers.csv"),
                "headers": ["keyword", "city", "business_name", "website", "email"]
            },
            "rejected_domains": {
                "path": config.get("output_files", {}).get("rejected_domains", "rejected_domains.csv"),
                "headers": ["domain", "reason"]
            },
            "logs": {
                "path": config.get("output_files", {}).get("logs", "logs.csv"),
                "headers": ["timestamp", "event", "details"]
            },
            "businesses_found": {
                "path": config.get("output_files", {}).get("businesses_found", "businesses_found.csv"),
                "headers": ["keyword", "city", "business_name", "website", "address", "phone"]
            }
        }
        
    async def init_files(self):
        """Creates the CSV files and writes headers if they don't exist."""
        for name, file_info in self.files.items():
            path = file_info["path"]
            if not os.path.exists(path):
                async with aiofiles.open(path, mode='w', newline='', encoding='utf-8') as f:
                    # We can't use csv.writer directly with aiofiles easily without a wrapper,
                    # but writing a simple header row as string is fine.
                    header_line = ",".join([f'"{h}"' for h in file_info["headers"]]) + "\n"
                    await f.write(header_line)

    async def write_row(self, file_key: str, row_dict: Dict[str, Any]):
        """Writes a single row to the specified CSV file asynchronously."""
        if file_key not in self.files:
            return
            
        file_info = self.files[file_key]
        headers = file_info["headers"]
        path = file_info["path"]
        
        # Prepare row data in the exact order of headers
        row_data = []
        for header in headers:
            val = row_dict.get(header, "")
            # Basic CSV escaping: wrap in quotes, escape existing quotes
            val_str = str(val).replace('"', '""')
            row_data.append(f'"{val_str}"')
            
        csv_line = ",".join(row_data) + "\n"
        
        async with self.lock:
            async with aiofiles.open(path, mode='a', newline='', encoding='utf-8') as f:
                await f.write(csv_line)
