import asyncio
import json
import os
import re
from urllib.parse import urlparse

from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError

DEFAULT_MESSAGE = "devam et kapsamlı bir işlem yaptır devam ediyorsa bozma takılma varsa tespit et düzelt"
GERMAN_MESSAGE = "mach weiter, führe einen umfassenden Vorgang aus; wenn es weiterläuft, störe es nicht; wenn es festhängt, erkenne es und behebe es"

DEFAULT_CONFIG = {
    "site_url": "https://senin-siten.com",
    "allowed_hosts": ["senin-siten.com"],
    "interval_seconds": 600,
    "message": DEFAULT_MESSAGE,
    "browser_profile_dir": "./browser-profile",
    "headless": False,
    "chat_input_selectors": [
        "textarea",
        "[contenteditable='true']",
        "input[type='text']"
    ],
    "send_button_texts": [
        "Gönder", "Gonder", "Send", "Submit", "Senden", "Absenden", "Weiter"
    ],
    "approve_button_texts": [
        "Onayla", "Evet", "Tamam", "Kabul Et",
        "Approve", "Confirm", "Yes", "OK",
        "Bestätigen", "Genehmigen", "Ja", "Akzeptieren", "Zustimmen", "Fortfahren", "Einverstanden"
    ],
    "in_progress_texts": [
        "devam ediyor", "işleniyor", "loading", "running", "processing", "please wait",
        "läuft", "wird verarbeitet", "verarbeitung", "bitte warten", "lädt", "in bearbeitung"
    ]
}


def load_config():
    path = os.environ.get("SITE_WATCHDOG_CONFIG", "automation/config.json")
    if not os.path.exists(path):
        return DEFAULT_CONFIG
    with open(path, "r", encoding="utf-8") as f:
        user_config = json.load(f)
    config = DEFAULT_CONFIG.copy()
    config.update(user_config)
    return config


def assert_allowed_url(url, allowed_hosts):
    host = urlparse(url).hostname or ""
    normalized = host.lower().removeprefix("www.")
    allowed = {h.lower().removeprefix("www.") for h in allowed_hosts}
    if normalized not in allowed:
        raise RuntimeError(f"Bu script sadece allowed_hosts içindeki sitelerde çalışır. host={host}, allowed={sorted(allowed)}")


def text_regex(words):
    escaped = [re.escape(w) for w in words]
    return re.compile(r"^(" + "|".join(escaped) + r")$", re.IGNORECASE)


async def click_approve_if_visible(page, config):
    pattern = text_regex(config["approve_button_texts"])
    candidates = [
        page.get_by_role("button", name=pattern),
        page.locator("button").filter(has_text=pattern),
        page.locator("[role='button']").filter(has_text=pattern),
        page.locator("input[type='button'], input[type='submit']")
    ]

    for locator in candidates:
        try:
            first = locator.first
            if await first.is_visible(timeout=700):
                await first.click()
                print("Onay butonu tıklandı.")
                return True
        except Exception:
            continue
    return False


async def page_has_in_progress_text(page, config):
    body_text = ""
    try:
        body_text = (await page.locator("body").inner_text(timeout=1000)).lower()
    except Exception:
        return False

    return any(token.lower() in body_text for token in config["in_progress_texts"])


async def find_chat_input(page, config):
    for selector in config["chat_input_selectors"]:
        try:
            locator = page.locator(selector).last
            if await locator.is_visible(timeout=1000):
                return locator
        except Exception:
            continue
    return None


async def click_send_if_present(page, config):
    pattern = text_regex(config["send_button_texts"])
    candidates = [
        page.get_by_role("button", name=pattern),
        page.locator("button").filter(has_text=pattern),
        page.locator("[role='button']").filter(has_text=pattern)
    ]
    for locator in candidates:
        try:
            first = locator.first
            if await first.is_visible(timeout=700):
                await first.click()
                return True
        except Exception:
            continue
    return False


async def send_message(page, config):
    if await page_has_in_progress_text(page, config):
        print("İşlem devam ediyor görünüyor; mesaj gönderilmedi.")
        return False

    chat_input = await find_chat_input(page, config)
    if chat_input is None:
        print("Chat input bulunamadı.")
        return False

    await chat_input.click()
    await chat_input.fill(config["message"])

    sent = await click_send_if_present(page, config)
    if not sent:
        await chat_input.press("Enter")

    print("Mesaj gönderildi.")
    return True


async def main():
    config = load_config()
    assert_allowed_url(config["site_url"], config["allowed_hosts"])

    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            config["browser_profile_dir"],
            headless=config["headless"],
        )
        page = context.pages[0] if context.pages else await context.new_page()

        page.on("dialog", lambda dialog: asyncio.create_task(dialog.accept()))
        await page.goto(config["site_url"], wait_until="domcontentloaded")

        print("Site watchdog başladı.")
        print("İlk çalıştırmada gerekiyorsa tarayıcıda manuel giriş yap.")

        while True:
            try:
                current_url = page.url
                assert_allowed_url(current_url, config["allowed_hosts"])
                await click_approve_if_visible(page, config)
                await send_message(page, config)
            except PlaywrightTimeoutError as e:
                print(f"Zaman aşımı: {e}")
            except Exception as e:
                print(f"Hata: {e}")

            await asyncio.sleep(int(config["interval_seconds"]))


if __name__ == "__main__":
    asyncio.run(main())
