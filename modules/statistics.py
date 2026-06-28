import time

class Statistics:
    def __init__(self):
        self.start_time = 0
        self.total_keywords = 0
        self.total_cities = 0
        
        self.processed_keywords = set()  # Set of processed keywords to track count uniquely
        self.processed_combinations = 0   # Total keyword + city pairs processed
        
        self.businesses_found = 0
        self.domains_visited = 0
        self.emails_found = 0
        self.business_emails = 0
        self.free_emails = 0
        self.rejected_domains = 0
        self.mx_valid_count = 0
        
        self.current_phase = 1
        self.total_websites_to_crawl = 0
        self.processed_websites = 0
        
    def start(self):
        self.start_time = time.time()
        
    def get_elapsed_time(self) -> str:
        if self.start_time == 0:
            return "00:00:00"
        elapsed = int(time.time() - self.start_time)
        hours, remainder = divmod(elapsed, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        
    def get_speed(self) -> float:
        """Returns domains visited per minute."""
        if self.start_time == 0:
            return 0.0
        elapsed_minutes = (time.time() - self.start_time) / 60
        if elapsed_minutes <= 0:
            return 0.0
        return round(self.domains_visited / elapsed_minutes, 2)
        
    def get_eta(self) -> str:
        """Estimates time remaining based on total combinations."""
        total_combinations = self.total_keywords * self.total_cities
        if total_combinations == 0 or self.start_time == 0:
            return "N/A"
            
        processed = self.processed_combinations
        if processed == 0:
            return "Calculating..."
            
        elapsed = time.time() - self.start_time
        time_per_combo = elapsed / processed
        remaining_combos = total_combinations - processed
        
        eta_seconds = int(time_per_combo * remaining_combos)
        hours, remainder = divmod(eta_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
