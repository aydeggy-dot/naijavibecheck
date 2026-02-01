"""Browser-based Instagram login using Playwright."""
import asyncio
import json
from pathlib import Path
from playwright.async_api import async_playwright

USERNAME = "moyolayo350"
PASSWORD = "Mayor1212@"

async def login_with_browser():
    print("Starting browser login...")
    print("=" * 50)

    async with async_playwright() as p:
        # Launch visible browser
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()

        # Go to Instagram
        print("Opening Instagram...")
        await page.goto("https://www.instagram.com/accounts/login/")

        print("\n" + "=" * 50)
        print("INSTRUCTIONS:")
        print("1. Log in manually if needed")
        print("2. Complete ANY verification Instagram asks for")
        print("3. Once you see your Instagram feed, come back here")
        print("=" * 50)
        print("\nWaiting for you to log in (up to 5 minutes)...")
        print("The script will detect when you're logged in.\n")

        # Wait for user to complete login (up to 5 minutes)
        try:
            # Wait until URL doesn't contain 'login' or 'auth'
            for i in range(300):  # 5 minutes (300 seconds)
                await page.wait_for_timeout(1000)
                current_url = page.url

                # Check if logged in (on feed or profile)
                if "instagram.com" in current_url and "login" not in current_url and "auth" not in current_url and "challenge" not in current_url:
                    print(f"\nDetected successful login! URL: {current_url}")
                    break

                if i % 10 == 0 and i > 0:
                    print(f"Still waiting... ({i} seconds)")

            # Give extra time for page to fully load
            await page.wait_for_timeout(3000)

            # Save cookies
            print("\nSaving session cookies...")
            cookies = await context.cookies()
            Path("sessions").mkdir(exist_ok=True)

            with open("sessions/instagram_cookies.json", "w") as f:
                json.dump(cookies, f, indent=2)
            print("Cookies saved to sessions/instagram_cookies.json")

            # Get sessionid cookie specifically
            sessionid = None
            for cookie in cookies:
                if cookie['name'] == 'sessionid':
                    sessionid = cookie['value']
                    break

            if sessionid:
                print(f"Session ID found: {sessionid[:20]}...")

                # Save in format instaloader can use
                print("\nTesting by fetching a post's comments...")
                await page.goto("https://www.instagram.com/p/DULsWrPjwef/")
                await page.wait_for_timeout(5000)

                print("Login complete! You can close this browser.")
            else:
                print("Warning: No session ID found in cookies")

        except Exception as e:
            print(f"Error: {e}")

        print("\n" + "=" * 50)
        print("Press Enter to close the browser...")
        print("=" * 50)
        input()
        await browser.close()

if __name__ == "__main__":
    asyncio.run(login_with_browser())
