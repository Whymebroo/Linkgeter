import argparse
import time
from pathlib import Path
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--query', type=str, required=True)
    parser.add_argument('--count', type=int, default=10)
    parser.add_argument('--sort', type=str, default='newest')
    args = parser.parse_args()

    # ساخت URL
    base_url = f"https://www.pornhub.com/video/search?search={args.query.replace(' ', '+')}"
    
    if args.sort == 'newest':
        base_url += "&o=cm"
    elif args.sort == 'mostviewed':
        base_url += "&o=mv"
    elif args.sort == 'rating':
        base_url += "&o=tr"

    output_dir = Path("PhResults")
    output_dir.mkdir(exist_ok=True)
    
    safe_name = "".join(c if c.isalnum() else "_" for c in args.query.lower())
    output_file = output_dir / f"pornhub_{safe_name}.txt"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        
        print(f"در حال باز کردن صفحه: {base_url}")
        page.goto(base_url, wait_until="networkidle", timeout=60000)
        time.sleep(5)   # صبر برای لود کامل (مهم)

        # اسکرول برای لود بیشتر ویدیوها
        for _ in range(3):
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            time.sleep(3)

        html = page.content()
        browser.close()

    # پارس کردن با BeautifulSoup
    soup = BeautifulSoup(html, 'html.parser')
    
    # سلکتورهای Pornhub (ممکنه بعداً عوض بشه)
    videos = soup.select('div.videoBox')[:args.count]
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(f"# نتایج جستجو: {args.query}\n")
        f.write(f"# مرتب‌سازی: {args.sort} | تعداد: {len(videos)}\n")
        f.write(f"# تاریخ: {time.strftime('%Y-%m-%d %H:%M')}\n\n")
        f.write("لینک | عنوان | مدت زمان | بازدید\n")
        f.write("-----|------|--------|-------\n")

        for video in videos:
            try:
                link_tag = video.select_one('a')
                title_tag = video.select_one('span.title')
                duration_tag = video.select_one('var.duration')
                views_tag = video.select_one('span.views')

                if not link_tag or not title_tag:
                    continue

                link = "https://www.pornhub.com" + link_tag.get('href', '')
                title = title_tag.get_text(strip=True)
                duration = duration_tag.get_text(strip=True) if duration_tag else "N/A"
                views = views_tag.get_text(strip=True) if views_tag else "N/A"

                f.write(f"{link} | {title} | {duration} | {views}\n")
            except:
                continue

    print(f"✅ تمام شد. {len(videos)} ویدیو استخراج شد و تو فایل ذخیره شد.")

if __name__ == "__main__":
    main()
