import asyncio
import aiohttp
from urllib.parse import urljoin
from bs4 import BeautifulSoup
import json

# Save results to a file
def save_results(results):
    with open("output.json", "w") as f:
        json.dump(results, f, indent=2)

# Fetch page content
async def fetch_page(session, url):
    try:
        async with session.get(url, timeout=10) as response:
            return await response.text()
    except Exception as e:
        print(f"Failed to fetch {url}: {e}")
        return None

# Crawl a domain
async def crawl_domain(domain, base_url, stop_event):
    visited = set()
    product_urls = set()
    queue = [base_url]

    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False)) as session:
        while queue and not stop_event.is_set():
            current_url = queue.pop(0)
            if current_url in visited:
                continue
            visited.add(current_url)

            html = await fetch_page(session, current_url)
            if not html:
                continue

            soup = BeautifulSoup(html, "html.parser")
            for link in soup.find_all("a", href=True):
                href = urljoin(base_url, link["href"])
                if is_product_url(href):
                    product_urls.add(href)
                elif href.startswith(base_url) and href not in visited:
                    queue.append(href)

    return list(product_urls)

# Check if the URL is a product URL
def is_product_url(url):
    patterns = ["/product/", "/item/", "/p/", "/collections"]
    return any(pattern in url for pattern in patterns)

async def main(domains, stop_event):
    results = {}
    for domain in domains:
        base_url = f"https://{domain}"
        results[domain] = await crawl_domain(domain, base_url, stop_event)
        if stop_event.is_set():
            break
    return results

if __name__ == "__main__":
    import signal
    from threading import Event

    stop_event = Event()

    def signal_handler(sig, frame):
        print("\nStopping the scraper...")
        stop_event.set()

    # Press Ctrl+C to stop in between and save to output.json
    signal.signal(signal.SIGINT, signal_handler)

    try:
        domains = ["amazon.in", "flipkart.com", "overlaysnow.com"]
        results = asyncio.run(main(domains, stop_event))
        save_results(results)
    except Exception as e:
        print(f"Error occurred: {e}")
