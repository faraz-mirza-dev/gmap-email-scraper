Build a production-ready Python CLI application called "Google Maps Business Email Scraper".

OBJECTIVE

The tool will:

1. Read keywords from keywords.txt
2. Read cities from cities.txt
3. Search Google Maps for every keyword + city combination
4. Collect business websites
5. Filter unwanted websites
6. Verify website relevance using keyword matching
7. Crawl website pages
8. Extract all available emails
9. Validate MX records
10. Export clean business emails into CSV files

Everything must run from the terminal.

==================================================
INPUT FILES
===========

keywords.txt

Example:

Vein Clinic
Orthopedic Clinic
Plastic Surgeon
Dentist
Implant Dentist

cities.txt

Example:

New York, NY
Miami, FL
Dallas, TX
Los Angeles, CA

==================================================
GOOGLE MAPS SEARCH
==================

For each keyword + city combination:

Search:

"<keyword> in <city>"

Extract:

* Business Name
* Website URL
* Address
* Phone Number (if available)

Requirements:

* Skip businesses without websites
* Remove duplicate websites
* Normalize domains
* Store unique domains only

==================================================
DOMAIN FILTERS
==============

Immediately reject:

.edu domains

.gov domains

Hospital websites

University websites

Schools

Colleges

Medical Centers

Healthcare Networks

Directories

Aggregators

Listing Websites

Job Boards

Examples:

hospital
medical center
health system
healthcare network
university
college
school
directory
listing
yelp
yellowpages
careers
indeed

Save rejected domains to:

rejected_domains.csv

==================================================
WEBSITE RELEVANCE CHECK
=======================

Visit homepage.

Download HTML.

Extract text.

Check if target keyword exists.

Use:

* Case insensitive matching
* Partial matching
* Similar phrase matching

Examples:

Keyword:
Plastic Surgeon

Accept:

Plastic Surgery
Plastic Surgeons
Cosmetic Surgery

Calculate relevance score.

Only continue if relevance score passes threshold.

==================================================
WEBSITE CRAWLING
================

Crawl:

Homepage

Contact Page

About Page

Team Page

Staff Page

Providers Page

Doctors Page

Services Pages

Locations Pages

Footer Links

Main Navigation Links

Internal Pages

Rules:

Only crawl same domain.

Maximum depth configurable.

Default depth:

3

==================================================
EMAIL EXTRACTION
================

Extract emails from:

HTML

Mailto Links

JavaScript

Structured Data

Contact Sections

Footer Sections

Regex Extraction

Normalize all emails.

Remove duplicates.

Ignore:

noreply

do-not-reply

test

example

fake

demo

==================================================
EMAIL PRIORITY
==============

Rank emails:

1 = info@

2 = contact@

3 = hello@

4 = sales@

5 = admin@

6 = support@

7 = owner or personal emails

Save:

Primary Email

All Emails

==================================================
FREE EMAIL FILTER
=================

If email domain is:

gmail.com
yahoo.com
hotmail.com
outlook.com
live.com
aol.com
icloud.com
proton.me

Save to:

free_email_providers.csv

Do NOT save these in business email CSV.

==================================================
MX RECORD VALIDATION
====================

For every business email:

Extract domain.

Check MX records using dnspython.

If MX records exist:

mx_valid = TRUE

Else:

mx_valid = FALSE

Only export emails where:

mx_valid = TRUE

==================================================
OUTPUT FILES
============

business_emails.csv

Columns:

keyword
city
business_name
website
primary_email
all_emails
mx_valid
address
phone
scraped_at

free_email_providers.csv

Columns:

keyword
city
business_name
website
email

rejected_domains.csv

Columns:

domain
reason

logs.csv

Columns:

timestamp
event
details

==================================================
PERFORMANCE REQUIREMENTS
========================

Must be optimized for speed.

Use:

Python 3.11+

asyncio

aiohttp

uvloop

selectolax

orjson

connection pooling

batch processing

URL deduplication

concurrent crawling

DNS caching

async MX validation

Process hundreds of websites concurrently.

Configurable concurrency:

50
100
200
500

==================================================
CLI MENU
========

python scraper.py

Menu:

1. Start Scraping
2. Resume Previous Run
3. View Statistics
4. Export Results
5. Clear Cache
6. Exit

==================================================
LIVE STATS
==========

Show:

Keywords Processed

Cities Processed

Businesses Found

Domains Visited

Emails Found

Business Emails

Free Emails

Rejected Domains

MX Valid Count

Current Speed

Elapsed Time

ETA

==================================================
ERROR HANDLING
==============

Handle:

Timeouts

Captcha Pages

Connection Failures

SSL Errors

Redirect Loops

DNS Errors

Rate Limits

Automatically retry failed requests.

==================================================
PROJECT STRUCTURE
=================

project/

scraper.py

config.json

keywords.txt

cities.txt

business_emails.csv

free_email_providers.csv

rejected_domains.csv

logs.csv

modules/

maps_search.py

domain_filter.py

website_checker.py

crawler.py

email_extractor.py

mx_validator.py

csv_writer.py

statistics.py

utils.py

==================================================
FINAL REQUIREMENT
=================

Generate complete production-ready source code.

Generate all Python files.

Generate installation instructions.

Generate requirements.txt.

Generate config.json.

Generate fully working CLI application with modular architecture, async crawling, Google Maps business extraction, email scraping, MX validation, filtering system, CSV export, logging, resume support, and maximum possible scraping speed.
