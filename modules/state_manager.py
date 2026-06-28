import aiosqlite
import os
import asyncio

class StateManager:
    def __init__(self, db_path: str = "state.db"):
        self.db_path = db_path
        self.lock = asyncio.Lock()
        
    async def init_db(self):
        """Initializes the SQLite database with necessary tables."""
        async with aiosqlite.connect(self.db_path, timeout=30.0) as db:
            await db.execute('''
                CREATE TABLE IF NOT EXISTS processed_searches (
                    search_key TEXT PRIMARY KEY
                )
            ''')
            await db.execute('''
                CREATE TABLE IF NOT EXISTS processed_domains (
                    domain TEXT PRIMARY KEY
                )
            ''')
            await db.execute('''
                CREATE TABLE IF NOT EXISTS processed_emails (
                    email TEXT PRIMARY KEY
                )
            ''')
            await db.commit()
            
            # Bulletproof duplicate prevention: 
            # If CSVs already exist, load all previously found domains and emails into the DB
            # so even if cache is cleared, we never scrape the same website or save the same email twice.
            import csv
            from modules.utils import get_base_domain
            for csv_file in ['business_emails.csv', 'free_emails.csv']:
                if os.path.exists(csv_file):
                    try:
                        with open(csv_file, 'r', encoding='utf-8') as f:
                            reader = csv.reader(f)
                            next(reader, None)  # Skip header
                            for row in reader:
                                if len(row) > 4:
                                    # Domain check
                                    domain = get_base_domain(row[3])
                                    if domain:
                                        await db.execute('INSERT OR IGNORE INTO processed_domains (domain) VALUES (?)', (domain,))
                                    # Email check
                                    email = row[4].strip().lower() if row[4] else ""
                                    if email:
                                        await db.execute('INSERT OR IGNORE INTO processed_emails (email) VALUES (?)', (email,))
                        await db.commit()
                    except Exception:
                        pass
            
    async def mark_search_processed(self, keyword: str, city: str):
        """Marks a keyword + city combination as processed."""
        search_key = f"{keyword}|{city}"
        async with self.lock:
            async with aiosqlite.connect(self.db_path, timeout=30.0) as db:
                await db.execute('INSERT OR IGNORE INTO processed_searches (search_key) VALUES (?)', (search_key,))
                await db.commit()

    async def is_search_processed(self, keyword: str, city: str) -> bool:
        """Checks if a search combination was already processed."""
        search_key = f"{keyword}|{city}"
        async with aiosqlite.connect(self.db_path, timeout=30.0) as db:
            async with db.execute('SELECT 1 FROM processed_searches WHERE search_key = ?', (search_key,)) as cursor:
                return await cursor.fetchone() is not None

    async def mark_domain_processed(self, domain: str):
        """Marks a domain as visited/processed."""
        async with self.lock:
            async with aiosqlite.connect(self.db_path, timeout=30.0) as db:
                await db.execute('INSERT OR IGNORE INTO processed_domains (domain) VALUES (?)', (domain,))
                await db.commit()
                
    async def is_domain_processed(self, domain: str) -> bool:
        """Checks if a domain was already processed."""
        async with aiosqlite.connect(self.db_path, timeout=30.0) as db:
            async with db.execute('SELECT 1 FROM processed_domains WHERE domain = ?', (domain,)) as cursor:
                return await cursor.fetchone() is not None
                
    async def mark_email_processed(self, email: str):
        """Marks an email as processed/saved."""
        email = email.strip().lower()
        async with self.lock:
            async with aiosqlite.connect(self.db_path, timeout=30.0) as db:
                await db.execute('INSERT OR IGNORE INTO processed_emails (email) VALUES (?)', (email,))
                await db.commit()
                
    async def is_email_processed(self, email: str) -> bool:
        """Checks if an email was already processed/saved."""
        email = email.strip().lower()
        async with aiosqlite.connect(self.db_path, timeout=30.0) as db:
            async with db.execute('SELECT 1 FROM processed_emails WHERE email = ?', (email,)) as cursor:
                return await cursor.fetchone() is not None
                
    async def clear_cache(self):
        """Deletes the state database."""
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
