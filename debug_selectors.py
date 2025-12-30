"""
Debug script to find the correct selectors for Instagram DM reactions and swipe replies
"""
import asyncio
from playwright.async_api import async_playwright
try:
    from playwright_stealth.stealth import stealth_async
except Exception:
    stealth_async = None
import json
import os
import dotenv

dotenv.load_dotenv()

async def debug_instagram_dm():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)

        # Try to load Playwright storage state for authenticated session
        storage_file = "sessions/7510461579_lofipapahuyr_state.json"
        storage_json = None
        if os.path.exists(storage_file):
            try:
                with open(storage_file, 'r') as f:
                    storage_json = json.load(f)
            except Exception:
                storage_json = None

        if storage_json:
            context = await browser.new_context(storage_state=storage_json, viewport={"width":1920, "height":1080})
        else:
            context = await browser.new_context(viewport={"width":1920, "height":1080})

        page = await context.new_page()
        if stealth_async:
            try:
                stealth = stealth_async(context)
                await stealth
            except Exception:
                pass

        # Go to Instagram DMs
        try:
            await page.goto("https://www.instagram.com/direct/", wait_until="load", timeout=30000)
        except Exception:
            # Fallback to main page then direct
            await page.goto("https://www.instagram.com/", wait_until="load")
            await asyncio.sleep(2)
            await page.goto("https://www.instagram.com/direct/", wait_until="load")
        await asyncio.sleep(3)
        
        print("\n" + "="*80)
        print("AVAILABLE MESSAGE SELECTORS")
        print("="*80)
        
        # Try different selectors
        selectors = [
            'div[role="article"]',
            '[data-testid="message-item"]',
            'div[class*="x1iyjqo2"]',
            'div[class*="message"]',
            'div[data-testid*="message"]',
            'li[role="presentation"]',
            'div[class*="x1ey2m1c"]',  # Common Instagram container
        ]
        
        for selector in selectors:
            elements = await page.query_selector_all(selector)
            print(f"\n✓ {selector}: Found {len(elements)} elements")
            if elements and len(elements) > 0:
                # Get first element's HTML
                html = await elements[0].evaluate("el => el.outerHTML.substring(0, 500)")
                print(f"  Sample HTML: {html[:200]}...")
        
        # Find buttons on messages
        print("\n" + "="*80)
        print("CHECKING MESSAGE BUTTONS")
        print("="*80)
        
        messages = await page.query_selector_all('div[role="article"]')
        if messages:
            msg = messages[-1]
            
            # Hover to reveal buttons
            await msg.hover()
            await asyncio.sleep(0.5)
            
            buttons = await msg.query_selector_all('button')
            print(f"\nFound {len(buttons)} buttons on last message")
            
            for i, btn in enumerate(buttons):
                label = await btn.get_attribute('aria-label') or "N/A"
                title = await btn.get_attribute('title') or "N/A"
                cls = await btn.get_attribute('class') or "N/A"
                print(f"  Button {i}: label='{label}' title='{title}'")
        
        # Look for emoji picker
        print("\n" + "="*80)
        print("EMOJI/REACTION PICKER")
        print("="*80)
        
        emoji_selectors = [
            '[aria-label*="❤"]',
            'button[aria-label*="heart"]',
            'div[role="option"]',
            '[data-testid*="emoji"]',
            'svg[aria-label*="heart"]',
        ]
        
        for selector in emoji_selectors:
            elements = await page.query_selector_all(selector)
            print(f"  {selector}: {len(elements)} found")
        
        print("\n✅ Debug complete - keep browser open to inspect manually (60s timeout)")
        # Also print full HTML and button attributes for the last matching message element
        try:
            # Find likely message elements again
            candidates = await page.query_selector_all('div[class*="x1iyjqo2"]')
            if not candidates:
                candidates = await page.query_selector_all('div[role="article"]')
            if candidates:
                last = candidates[-1]
                full_html = await last.evaluate('el => el.outerHTML')
                print('\n' + '='*80)
                print('LAST MESSAGE FULL HTML')
                print('='*80)
                print(full_html[:2000])

                print('\n' + '='*80)
                print('BUTTONS INSIDE LAST MESSAGE')
                print('='*80)
                buttons = await last.query_selector_all('button')
                for i, btn in enumerate(buttons):
                    label = await btn.get_attribute('aria-label') or ''
                    title = await btn.get_attribute('title') or ''
                    cls = await btn.get_attribute('class') or ''
                    text = await btn.inner_text() or ''
                    print(f"Button {i}: label='{label}' title='{title}' class='{cls}' text='{text[:80]}'")
        except Exception as e:
            print('Error while dumping last message details:', e)

        await asyncio.sleep(3)
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(debug_instagram_dm())
