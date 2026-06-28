import logging
logging.getLogger("asyncio").setLevel(logging.CRITICAL)
logging.getLogger("aiohttp").setLevel(logging.CRITICAL)
import asyncio
import aiohttp
import json
import os
import sys
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.live import Live
from rich.panel import Panel
from rich.prompt import Prompt

# Removed uvloop because it is incompatible with Playwright

from modules.maps_search import MapsSearch
from modules.domain_filter import is_rejected_domain
from modules.website_checker import WebsiteChecker
from modules.crawler import Crawler
from modules.email_extractor import EmailExtractor
from modules.mx_validator import MXValidator
from modules.csv_writer import CSVWriter
from modules.state_manager import StateManager
from modules.statistics import Statistics
from modules.utils import get_base_domain

console = Console()

class ScraperOrchestrator:
    def __init__(self):
        self.seen_domains = set()
        self.load_config()
        self.stats = Statistics()
        self.state_manager = StateManager(self.config.get('db_path', 'state.db'))
        self.csv_writer = CSVWriter(self.config)
        self.maps_search = MapsSearch(self.config)
        self.website_checker = WebsiteChecker(self.config)
        self.crawler = Crawler(self.config)
        self.mx_validator = MXValidator()
        self.email_extractor = EmailExtractor()
        
        self.keywords = []
        self.cities = []
        self.load_inputs()

    def load_config(self):
        try:
            with open('config.json', 'r') as f:
                self.config = json.load(f)
        except Exception:
            self.config = {
                "concurrency": 100,
                "timeout_seconds": 15
            }

    def load_inputs(self):
        try:
            with open(self.config.get('keywords_file', 'keywords.txt'), 'r') as f:
                self.keywords = [line.strip() for line in f if line.strip()]
        except FileNotFoundError:
            pass
            
        try:
            with open(self.config.get('cities_file', 'cities.txt'), 'r') as f:
                self.cities = [line.strip() for line in f if line.strip()]
        except FileNotFoundError:
            pass
            
        self.stats.total_keywords = len(self.keywords)
        self.stats.total_cities = len(self.cities)

    def generate_stats_table(self) -> Table:
        if self.stats.current_phase == 1:
            table = Table(title="Phase 1/2: Google Maps Search (Live Statistics)")
            table.add_column("Metric", style="cyan")
            table.add_column("Value", style="magenta")
            
            total_combos = self.stats.total_keywords * self.stats.total_cities
            table.add_row("Keywords Processed", f"{len(self.stats.processed_keywords)}/{self.stats.total_keywords}")
            table.add_row("Combinations Processed", f"{self.stats.processed_combinations}/{total_combos}")
            table.add_row("Businesses Found", str(self.stats.businesses_found))
            table.add_row("Elapsed Time", self.stats.get_elapsed_time())
            table.add_row("ETA", self.stats.get_eta())
            return table
        else:
            table = Table(title="Phase 2/2: Email Extraction (Live Statistics)")
            table.add_column("Metric", style="cyan")
            table.add_column("Value", style="magenta")
            
            table.add_row("Websites Processed", f"{self.stats.processed_websites}/{self.stats.total_websites_to_crawl}")
            table.add_row("Domains Visited", str(self.stats.domains_visited))
            table.add_row("Emails Found", str(self.stats.emails_found))
            table.add_row("Business Emails (Valid MX)", f"{self.stats.business_emails} ({self.stats.mx_valid_count})")
            table.add_row("Free Emails", str(self.stats.free_emails))
            table.add_row("Rejected Domains", str(self.stats.rejected_domains))
            table.add_row("Current Speed (Domains/min)", str(self.stats.get_speed()))
            table.add_row("Elapsed Time", self.stats.get_elapsed_time())
            return table

    async def process_business(self, business: dict, keyword: str, city: str, session: aiohttp.ClientSession):
        domain = get_base_domain(business['website'])
        if not domain:
            return
            
        if await self.state_manager.is_domain_processed(domain):
            return
            
        await self.state_manager.mark_domain_processed(domain)
        self.stats.domains_visited += 1

        # 1. Filter Domain
        is_rejected, reason = is_rejected_domain(domain, business.get('business_name', ''))
        if is_rejected:
            self.stats.rejected_domains += 1
            await self.csv_writer.write_row("rejected_domains", {"domain": domain, "reason": reason})
            return

        # 2. Check Relevance
        is_relevant, score, html = await self.website_checker.check_relevance(business['website'], keyword, session)
        if not is_relevant:
            # We can log irrelevant domains if we want
            return

        # 3. Crawl for Emails
        emails = await self.crawler.crawl_website(business['website'], session)
        if not emails:
            return
            
        self.stats.emails_found += len(emails)

        # 4. Extract and Filter Emails
        business_emails_set = set()
        free_emails_set = set()
        
        for email in emails:
            if self.email_extractor.is_free_email(email):
                if await self.state_manager.is_email_processed(email):
                    continue
                await self.state_manager.mark_email_processed(email)
                
                free_emails_set.add(email)
                self.stats.free_emails += 1
                await self.csv_writer.write_row("free_emails", {
                    "keyword": keyword, "city": city, "business_name": business.get('business_name', ''),
                    "website": business['website'], "email": email
                })
            else:
                business_emails_set.add(email)

        # 5. Process Business Emails
        if business_emails_set:
            primary_email, sorted_emails = self.email_extractor.rank_emails(business_emails_set)
            
            # Write a separate row for each email found
            for email_address in sorted_emails:
                email_domain = email_address.split('@')[1]
                base_domain = get_base_domain(business['website'])
                
                # NEW LOGIC: Cross-domain relevance check
                # If the email domain is different from the website domain and is not a free provider
                if email_domain != base_domain and not self.email_extractor.is_free_email(email_address):
                    is_relevant, _, _ = await self.website_checker.check_relevance(f"http://{email_domain}", keyword, session)
                    if not is_relevant:
                        continue # Drop this email, the domain is not related to the keyword
                
                # Check globally if we've already saved this email
                if await self.state_manager.is_email_processed(email_address):
                    continue
                
                # MX Validation on the domain
                mx_valid = await self.mx_validator.is_valid_mx(email_domain)
                
                if mx_valid:
                    self.stats.mx_valid_count += 1
                    self.stats.business_emails += 1
                    
                    # Mark email as saved globally
                    await self.state_manager.mark_email_processed(email_address)
                    
                    await self.csv_writer.write_row("business_emails", {
                        "keyword": keyword, "city": city, "business_name": business.get('business_name', ''),
                        "website": business['website'], "primary_email": email_address,
                        "all_emails": "", # Left blank as per user request
                        "mx_valid": "TRUE",
                        "address": business.get('address', ''), "phone": business.get('phone', ''),
                        "scraped_at": datetime.now().isoformat()
                    })
                    
                    await self.csv_writer.write_row("logs", {
                        "timestamp": datetime.now().isoformat(),
                        "event": "SUCCESS",
                        "details": f"Saved {email_address} for {business.get('business_name', '')}"
                    })

    async def maps_worker(self, queue: asyncio.Queue, session: aiohttp.ClientSession):
        while True:
            try:
                keyword, city = queue.get_nowait()
            except asyncio.QueueEmpty:
                break
                
            try:
                if await self.state_manager.is_search_processed(keyword, city):
                    self.stats.processed_combinations += 1
                    self.stats.processed_keywords.add(keyword)
                    continue
                    
                async for business in self.maps_search.search(keyword, city, session):
                    self.stats.businesses_found += 1
                    
                    website = business.get("website")
                    if website:
                        domain = get_base_domain(website)
                        if domain:
                            if domain in self.seen_domains:
                                continue # Pure deduplication: skip writing this domain to CSV
                            self.seen_domains.add(domain)
                            
                    await self.csv_writer.write_row("businesses_found", {
                        "keyword": keyword,
                        "city": city,
                        "business_name": business["name"],
                        "website": business.get("website", ""),
                        "address": business.get("address", ""),
                        "phone": business.get("phone", "")
                    })
                    
                await self.state_manager.mark_search_processed(keyword, city)
                self.stats.processed_combinations += 1
                self.stats.processed_keywords.add(keyword)
            except Exception as e:
                import traceback
                print(f"Exception in maps_worker: {e}")
                traceback.print_exc()
            finally:
                queue.task_done()

    async def email_worker(self, queue: asyncio.Queue, session: aiohttp.ClientSession):
        while True:
            try:
                business = queue.get_nowait()
            except asyncio.QueueEmpty:
                break
                
            try:
                await self.process_business(business, business.get('keyword', ''), business.get('city', ''), session)
                self.stats.processed_websites += 1
            except Exception as e:
                pass
            finally:
                queue.task_done()

    async def run_phase_1(self, session: aiohttp.ClientSession):
        self.stats.current_phase = 1
        queue = asyncio.Queue()
        for kw in self.keywords:
            for city in self.cities:
                queue.put_nowait((kw, city))
                
        workers = [asyncio.create_task(self.maps_worker(queue, session)) for _ in range(10)]
        
        with Live(self.generate_stats_table(), refresh_per_second=2) as live:
            while not queue.empty() or any(not w.done() for w in workers):
                live.update(self.generate_stats_table())
                await asyncio.sleep(0.5)
                
        await queue.join()
        for w in workers:
            w.cancel()

    async def run_phase_2(self, session: aiohttp.ClientSession):
        self.stats.current_phase = 2
        self.stats.start() # Reset timer for speed calculations
        
        businesses = []
        try:
            import csv
            with open(self.csv_writer.files["businesses_found"]["path"], 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    businesses.append(row)
        except Exception:
            pass
            
        unique_businesses = []
        seen_domains = set()
        for b in businesses:
            domain = get_base_domain(b.get('website', ''))
            if domain and domain not in seen_domains:
                seen_domains.add(domain)
                unique_businesses.append(b)
                
        self.stats.total_websites_to_crawl = len(unique_businesses)
        self.stats.processed_websites = 0
        
        queue = asyncio.Queue()
        for b in unique_businesses:
            queue.put_nowait(b)
            
        concurrency = self.config.get('concurrency', 100)
        workers = [asyncio.create_task(self.email_worker(queue, session)) for _ in range(concurrency)]
        
        with Live(self.generate_stats_table(), refresh_per_second=2) as live:
            while not queue.empty() or any(not w.done() for w in workers):
                live.update(self.generate_stats_table())
                await asyncio.sleep(0.5)
                
        await queue.join()
        for w in workers:
            w.cancel()

    async def run_scraper(self, resume=False, skip_phase_1=False, skip_phase_2=False):
        if not self.keywords or not self.cities:
            console.print("[red]Error: keywords.txt or cities.txt is empty.[/red]")
            return
            
        # Reset stats for a fresh visual start
        self.stats = Statistics()

        await self.state_manager.init_db()
        await self.csv_writer.init_files()
        
        # Pre-load seen domains from businesses_found.csv so we never duplicate across resumes
        try:
            import csv
            with open(self.csv_writer.files["businesses_found"]["path"], 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    website = row.get("website")
                    if website:
                        domain = get_base_domain(website)
                        if domain:
                            self.seen_domains.add(domain)
        except Exception:
            pass
        
        self.stats.start()
        
        concurrency = self.config.get('concurrency', 100)
        connector = aiohttp.TCPConnector(limit=concurrency, ssl=False)
        
        async with aiohttp.ClientSession(connector=connector) as session:
            if not skip_phase_1:
                console.print("\n[bold cyan]--- Starting Phase 1: Google Maps Search ---[/bold cyan]")
                await self.run_phase_1(session)
            
            if not skip_phase_2:
                console.print("\n[bold cyan]--- Starting Phase 2: Email Extraction ---[/bold cyan]")
                await self.run_phase_2(session)
            
        console.print("[green]Scraping Completed![/green]")
        console.print(self.generate_stats_table())

def print_menu():
    console.print(Panel("[bold cyan]Google Maps Business Email Scraper[/bold cyan]"))
    console.print("1. Start Scraping (Phase 1 + Phase 2)")
    console.print("2. Resume Previous Run")
    console.print("3. Extract Emails Only (Skip Phase 1)")
    console.print("4. View Statistics")
    console.print("5. Clear Cache")
    console.print("6. Exit")

async def main():
    orchestrator = ScraperOrchestrator()
    
    while True:
        print_menu()
        choice = Prompt.ask("Select an option", choices=["1", "2", "3", "4", "5", "6"])
        
        if choice == '1':
            await orchestrator.run_scraper(resume=False)
        elif choice == '2':
            await orchestrator.run_scraper(resume=True)
        elif choice == '3':
            await orchestrator.run_scraper(skip_phase_1=True)
        elif choice == '4':
            orchestrator.stats = Statistics()
            console.print(orchestrator.generate_stats_table())
        elif choice == '5':
            await orchestrator.state_manager.clear_cache()
            console.print("[green]Cache cleared successfully![/green]")
        elif choice == '6':
            break

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        console.print("\n[yellow]Scraping stopped by user.[/yellow]")
        sys.exit(0)
