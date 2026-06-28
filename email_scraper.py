import logging
logging.getLogger("asyncio").setLevel(logging.CRITICAL)
logging.getLogger("aiohttp").setLevel(logging.CRITICAL)
import asyncio
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from scraper import ScraperOrchestrator

console = Console()

def print_menu():
    console.print(Panel("[bold cyan]Email Extraction Worker[/bold cyan]"))
    console.print("1. Start Email Scraping")
    console.print("2. Clear Cache (Reset Scraped Domains Memory)")
    console.print("3. Exit")

async def main():
    orchestrator = ScraperOrchestrator()
    
    while True:
        print_menu()
        choice = Prompt.ask("Select an option", choices=["1", "2", "3"])
        
        if choice == '1':
            await orchestrator.run_scraper(skip_phase_1=True)
        elif choice == '2':
            import os
            try:
                os.remove("state.db")
                console.print("[green]Cache cleared successfully![/green]")
            except FileNotFoundError:
                console.print("[yellow]Cache is already clear![/yellow]")
            except Exception as e:
                console.print(f"[red]Error clearing cache: {e}[/red]")
        elif choice == '3':
            console.print("\n[yellow]Exiting...[/yellow]")
            break

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        console.print("\n[yellow]Stopped by user.[/yellow]")
