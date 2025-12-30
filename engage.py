#!/usr/bin/env python3
"""
Pure engagement script with multiple strategies:
1. Aggressive hover + button detection with extended waits
2. Keyboard navigation (Tab, Enter) to trigger replies
3. Network API interception to detect Instagram's internal API calls

Usage: python engage.py --thread-url <URL> --storage-state <STATE_FILE>
"""
import argparse
import asyncio
import json
import os
import sys
import time
from playwright.async_api import async_playwright

# Redirect stdout/stderr to a logfile
try:
    log_path = os.path.join(os.getcwd(), "engage.log")
    log_fd = open(log_path, "a", buffering=1)
    sys.stdout = log_fd
    sys.stderr = log_fd
except Exception:
    pass

MOBILE_UA = "Mozilla/5.0 (Linux; Android 13; vivo V60) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Mobile Safari/537.36"
MOBILE_VIEWPORT = {"width": 412, "height": 915}

LAUNCH_ARGS = [
    "--disable-dev-shm-usage",
    "--no-sandbox",
    "--disable-gpu",
    "--disable-extensions",
    "--disable-sync",
    "--disable-background-networking",
    "--disable-background-timer-throttling",
    "--disable-renderer-backgrounding",
    "--mute-audio",
]

# Track captured API calls
captured_apis = []


async def on_response(response):
    """Capture Instagram API calls for direct endpoint usage"""
    global captured_apis
    url = response.url
    if 'instagram.com' in url and ('graphql' in url or 'api' in url.lower()):
        try:
            method = response.request.method
            if method in ['POST', 'PUT']:
                captured_apis.append({
                    'url': url,
                    'method': method,
                    'status': response.status,
                    'timestamp': time.time()
                })
                if len(captured_apis) <= 5:  # Log first 5 API calls
                    print(f"  🔍 API: {method} {url[-80:]}")
        except Exception:
            pass


async def engage_mode(thread_url: str, storage_state: str, reply_text: str = ''):
    """Multi-strategy engagement: hover+wait, keyboard nav, and API tracking"""
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True, args=LAUNCH_ARGS)

            # Load session
            try:
                with open(storage_state, 'r') as f:
                    storage_json = json.load(f)
            except Exception as e:
                print(f"❌ Failed to load session: {e}")
                return

            context = await browser.new_context(
                storage_state=storage_json,
                user_agent=MOBILE_UA,
                viewport=MOBILE_VIEWPORT,
                is_mobile=True,
                has_touch=True,
            )

            page = await context.new_page()

            # Set up API response listener
            page.on("response", on_response)

            print("🔥 ENGAGEMENT MODE ACTIVATED (3 strategies: hover+wait, keyboard, API)")
            print(f"📍 Target: {thread_url[:60]}...")
            print("⏳ Connecting...")

            try:
                await page.goto("https://www.instagram.com/", timeout=30000)
                await page.goto(thread_url, timeout=30000)
                await asyncio.sleep(3)
            except Exception as e:
                print(f"❌ Failed to connect: {e}")
                await browser.close()
                return

            print("✅ Connected! Monitoring messages...\n")
            message_count = 0
            reaction_count = 0
            reply_count = 0

            selectors = [
                'div[role="article"]',
                '[data-testid="message-item"]',
                'div[class*="x1iyjqo2"]',
                'div[class*="x1ey2m1c"]',
            ]

            while True:
                try:
                    # Find messages (re-query each iteration)
                    locator_list = []
                    used_sel = None

                    for sel in selectors:
                        try:
                            loc = page.locator(sel)
                            cnt = await loc.count()
                            if cnt > 0:
                                used_sel = sel
                                locator_list = [loc.nth(i) for i in range(cnt)]
                                break
                        except Exception:
                            continue

                    if not locator_list:
                        locator_list = []

                    current_count = len(locator_list)
                    if current_count > message_count:
                        new_count = current_count - message_count
                        print(f"📨 +{new_count} new message(s) | Total: {current_count} | ❤️ {reaction_count} | 💬 {reply_count} | selector={used_sel}")
                        message_count = current_count

                        # Process newly added messages
                        for msg_idx in range(current_count - new_count, current_count):
                            try:
                                msg_loc = locator_list[msg_idx]
                                processed = False

                                # ============ STRATEGY 1: Aggressive hover + extended wait ============
                                try:
                                    await msg_loc.hover()
                                    # Extended waits to let buttons render
                                    for wait_iter in range(5):
                                        await asyncio.sleep(0.3)
                                        btn_loc = msg_loc.locator('button')
                                        btn_count = await btn_loc.count()
                                        
                                        if btn_count > 0:
                                            print(f"    ✓ Found {btn_count} buttons after hover (wait {wait_iter + 1}/5)")
                                            
                                            for btn_idx in range(btn_count):
                                                try:
                                                    btn = btn_loc.nth(btn_idx)
                                                    lbl = (await btn.get_attribute('aria-label') or '').lower()
                                                    
                                                    if any(x in lbl for x in ['react', 'emoji', 'like', 'heart']):
                                                        await btn.click()
                                                        await asyncio.sleep(0.2)
                                                        
                                                        # Try to click heart in picker
                                                        for _ in range(3):
                                                            heart = page.locator('button[aria-label*="❤"]')
                                                            if await heart.count() == 0:
                                                                heart = page.locator('[aria-label*="❤"]')
                                                            
                                                            if await heart.count() > 0:
                                                                await heart.first.click()
                                                                reaction_count += 1
                                                                print('    ❤️ Heart reaction added (hover strategy)')
                                                                processed = True
                                                                break
                                                        if processed:
                                                            break
                                                    
                                                    elif any(x in lbl for x in ['reply', 'respond']):
                                                        await btn.click()
                                                        reply_count += 1
                                                        print('    💬 Reply triggered (hover strategy)')
                                                        processed = True
                                                        break
                                                except Exception:
                                                    continue
                                            
                                            if processed:
                                                break
                                except Exception as e:
                                    pass

                                if processed:
                                    await asyncio.sleep(0.5)
                                    continue

                                # ============ STRATEGY 2: Keyboard navigation (Tab + Enter) ============
                                try:
                                    await msg_loc.focus()
                                    await asyncio.sleep(0.1)
                                    
                                    # Try keyboard shortcuts for reply (Instagram uses keyboard shortcuts)
                                    await page.keyboard.press('Tab')
                                    await asyncio.sleep(0.1)
                                    await page.keyboard.press('Enter')
                                    await asyncio.sleep(0.3)
                                    
                                    # Check if reply box appeared
                                    reply_box = page.locator('div[role="textbox"], textarea, [contenteditable="true"]')
                                    if await reply_box.count() > 0:
                                        # Auto-type a quick reply and send
                                        try:
                                            rb = reply_box.first
                                            await rb.focus()
                                            await page.keyboard.type(reply_text or 'Nice! 👋', delay=30)
                                            await page.keyboard.press('Enter')
                                            reply_count += 1
                                            print('    💬 Reply sent (keyboard strategy)')
                                            processed = True
                                        except Exception:
                                            reply_count += 1
                                            print('    💬 Reply activated (keyboard strategy - send failed)')
                                            processed = True
                                except Exception:
                                    pass

                                if processed:
                                    continue

                                # ============ STRATEGY 3: Right-click context menu ============
                                try:
                                    await msg_loc.click(button='right')
                                    await asyncio.sleep(0.3)
                                    
                                    reply_loc = page.locator('text=Reply')
                                    if await reply_loc.count() == 0:
                                        reply_loc = page.locator('[role="menuitem"], [role="button"]')
                                    
                                    if await reply_loc.count() > 0:
                                        await reply_loc.first.click()
                                        # wait for reply box then send
                                        await asyncio.sleep(0.25)
                                        reply_box = page.locator('div[role="textbox"], textarea, [contenteditable="true"]')
                                        if await reply_box.count() > 0:
                                            try:
                                                rb = reply_box.first
                                                await rb.focus()
                                                await page.keyboard.type(reply_text or 'Nice! 👋', delay=30)
                                                await page.keyboard.press('Enter')
                                                reply_count += 1
                                                print('    💬 Reply sent (context-menu)')
                                                processed = True
                                            except Exception:
                                                reply_count += 1
                                                print('    💬 Reply activated (context-menu - send failed)')
                                                processed = True
                                        else:
                                            reply_count += 1
                                            print('    💬 Reply triggered (context-menu - no box)')
                                            processed = True
                                except Exception:
                                    pass

                                if processed:
                                    continue

                                # ============ STRATEGY 4: Swipe gesture ============
                                try:
                                    box = await msg_loc.bounding_box()
                                    if box:
                                        start_x = box['x'] + box['width'] * 0.85
                                        start_y = box['y'] + box['height'] / 2
                                        end_x = box['x'] + box['width'] * 0.15
                                        
                                        await page.mouse.move(start_x, start_y)
                                        await page.mouse.down()
                                        for i in range(1, 10):
                                            nx = start_x + (end_x - start_x) * (i / 10)
                                            await page.mouse.move(nx, start_y)
                                            await asyncio.sleep(0.03)
                                        await page.mouse.up()
                                        await asyncio.sleep(0.5)
                                        
                                        # Check for reply UI
                                        reply_box = page.locator('div[role="textbox"], textarea')
                                        if await reply_box.count() > 0:
                                            reply_count += 1
                                            print('    💬 Swipe-reply triggered (gesture strategy)')
                                except Exception:
                                    pass

                            except Exception as e:
                                pass

                    # Print API insights every 20 iterations
                    if message_count % 20 == 0 and message_count > 0 and captured_apis:
                        print(f"  🔍 Captured {len(captured_apis)} API calls so far")

                    await asyncio.sleep(2)

                except KeyboardInterrupt:
                    print('\n\n🛑 Engagement stopped')
                    print(f'📊 Final: {message_count} messages | {reaction_count} ❤️ | {reply_count} 💬')
                    if captured_apis:
                        print(f'📡 Captured {len(captured_apis)} API calls - could automate with direct calls')
                    break
                except Exception as e:
                    await asyncio.sleep(2)

    except Exception as e:
        print(f"❌ Fatal error: {e}")
    finally:
        try:
            await browser.close()
        except Exception:
            pass
        except Exception:
            pass


async def main():
    parser = argparse.ArgumentParser(description="Pure engagement mode - react and swipe replies only")
    parser.add_argument('--thread-url', required=True, help='Instagram DM thread URL')
    parser.add_argument('--storage-state', required=True, help='Path to storage state JSON file')
    parser.add_argument('--reply-text', required=False, default='', help='Text to send as reply when reply box appears')

    args = parser.parse_args()

    if not os.path.exists(args.storage_state):
        print(f"❌ Storage state file not found: {args.storage_state}")
        return

    if 'instagram.com' not in args.thread_url:
        print(f"❌ Invalid Instagram URL")
        return

    await engage_mode(args.thread_url, args.storage_state, reply_text=args.reply_text)


if __name__ == "__main__":
    asyncio.run(main())
