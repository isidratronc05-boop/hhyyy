#!/usr/bin/env python3
"""
Simple test to verify msg.py can run and detect the right selectors.
Run this to debug why reactions aren't working.
"""
import subprocess
import time
import os
import sys

# Check if we have a valid session
session_file = "sessions/7510461579_lofipapahuyr_state.json"
if not os.path.exists(session_file):
    print("❌ Session file not found:", session_file)
    sys.exit(1)

print("✅ Session file found")
print("\nTo test message sending:")
print("1. Send /attack command to bot on Telegram")
print("2. Choose 'dm' mode")
print("3. Enter target username")
print("4. Send messages like: hello & test & hi")
print("\nThe bot will then:")
print("  💬 Send each message")
print("  💓 Try to add hearts to sent message")
print("  🔄 Try to react to incoming messages")
print("\nWatch /workspaces/bot/bot.log for detailed output")
print("\n" + "="*60)
print("Bot is running on PID:", end=" ")
os.system("ps aux | grep 'python spbot5' | grep -v grep | awk '{print $2}'")
print("\nCheck logs with: tail -50 /workspaces/bot/bot.log")
