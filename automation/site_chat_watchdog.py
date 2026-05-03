import asyncio
import hashlib
import json
import os
import re
import time
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError

DEFAULT_MESSAGE = "devam et kapsamlı bir işlem yaptır devam ediyorsa bozma takılma varsa tespit et düzelt"
GERMAN_MESSAGE = "mach weiter, führe einen umfassenden Vorgang aus; wenn es weiterläuft, störe es nicht; wenn es festhängt, erkenne es und behebe es"

DEFAULT_CONFIG = {
    "site_url": "https://senin-siten.com",
    "allowed_hosts": ["senin-siten.com"],

    "watch_interval_seconds": 10,
    "send_interval_seconds": 600,
    "send_when_busy": False,

    "reload_when_page_frozen": True,
    "reload_when_stuck": True,
    "stuck_same_page_cycles": 6,
    "input_missing_reload_cycles": 3,
    "js_timeout_seconds": 5,
    "navigation_timeout_ms": 30000,
    "reload_backoff_seconds": 15,
    "max_consecutive_reloads": 5,

    "message": DEFAULT_MESSAGE,
    "browser_profile_dir": "./browser-profile",
    "headless": False,
    "screenshot_on_recovery": True,
    "screenshot_dir": "./screenshots",

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


def log(message):
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {message}", flush=True)


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


def scope_name(scope):
    return getattr(scope, "url", "main-page")


def all_scopes(page):
    scopes = [page]
    for frame in page.frames:
        if frame != page.main_frame:
            scopes.append(frame)
    return scopes


async def is_page_responsive(page, config):
    try:
        await asyncio.wait_for(page.evaluate("() => Date.now()"), timeout=float(config["js_timeout_seconds"]))
        return True
    except Exception:
        return False


async def take_recovery_screenshot(page, config, reason):
    if not config.get("screenshot_on_recovery"):
        return
    try:
        screenshot_dir = Path(config["screenshot_dir"])
        screenshot_dir.mkdir(parents=True, exist_ok=True)
        safe_reason = re.sub(r"[^a-zA-Z0-9_-]+", "_", reason)[:60]
        path = screenshot_dir / f"recovery_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{safe_reason}.png"
        await page.screenshot(path=str(path), full_page=True)
        log(f"Kurtarma ekran görüntüsü kaydedildi: {path}")
    except Exception as e:
        log(f"Ekran görüntüsü alınamadı: {e}")


async def recover_page(context, page, config, reason, consecutive_reloads):
    if consecutive_reloads >= int(config["max_consecutive_reloads"]):
        wait_seconds = int(config["reload_backoff_seconds"])
        log(f"Çok fazla kurtarma denemesi oldu. {wait_seconds} sn bekleniyor. Neden: {reason}")
        await asyncio.sleep(wait_seconds)

    try:
        if page and not page.is_closed():
            await take_recovery_screenshot(page, config, reason)
            log(f"Sayfa yenileniyor. Neden: {reason}")
            await page.reload(wait_until="domcontentloaded", timeout=int(config["navigation_timeout_ms"]))
            return page
    except Exception as e:
        log(f"Reload başarısız, site tekrar açılacak: {e}")

    page = await context.new_page()
    page.on("dialog", lambda dialog: asyncio.create_task(handle_dialog(dialog)))
    await page.goto(config["site_url"], wait_until="domcontentloaded", timeout=int(config["navigation_timeout_ms"]))
    return page


async def handle_dialog(dialog):
    try:
        log(f"Native dialog yakalandı ve kabul edildi: {dialog.message}")
        await dialog.accept()
    except Exception as e:
        log(f"Native dialog kabul edilemedi: {e}")


async def click_locator_if_visible(locator, timeout_ms=700):
    try:
        first = locator.first
        if await first.is_visible(timeout=timeout_ms):
            await first.click()
            return True
    except Exception:
        return False
    return False


async def click_approve_in_scope(scope, config):
    pattern = text_regex(config["approve_button_texts"])
    candidates = [
        scope.get_by_role("button", name=pattern),
        scope.locator("button").filter(has_text=pattern),
        scope.locator("[role='button']").filter(has_text=pattern),
        scope.locator("a").filter(has_text=pattern),
    ]

    for locator in candidates:
        if await click_locator_if_visible(locator):
            log(f"Onay butonu tıklandı. Scope: {scope_name(scope)}")
            return True

    input_buttons = scope.locator("input[type='button'], input[type='submit']")
    try:
        count = await input_buttons.count()
        allowed = {w.lower() for w in config["approve_button_texts"]}
        for idx in range(min(count, 20)):
            item = input_buttons.nth(idx)
            value = ((await item.get_attribute("value")) or "").strip().lower()
            aria = ((await item.get_attribute("aria-label")) or "").strip().lower()
            title = ((await item.get_attribute("title")) or "").strip().lower()
            if value in allowed or aria in allowed or title in allowed:
                if await item.is_visible(timeout=500):
                    await item.click()
                    log(f"Input onay butonu tıklandı. Scope: {scope_name(scope)}")
                    return True
    except Exception:
        pass

    return False


async def click_approve_if_visible(page, config):
    clicked = False
    for scope in all_scopes(page):
        try:
            clicked = await click_approve_in_scope(scope, config) or clicked
        except Exception:
            continue
    return clicked


async def get_body_text(page):
    try:
        return await page.locator("body").inner_text(timeout=1500)
    except Exception:
        return ""


async def page_has_in_progress_text(page, config):
    body_text = (await get_body_text(page)).lower()
    return any(token.lower() in body_text for token in config["in_progress_texts"])


async def page_signature(page):
    text = await get_body_text(page)
    compact = " ".join(text.split())[:10000]
    raw = f"{page.url}|{compact}"
    return hashlib.sha256(raw.encode("utf-8", errors="ignore")).hexdigest()


async def find_chat_input_in_scope(scope, config):
    for selector in config["chat_input_selectors"]:
        try:
            locator = scope.locator(selector).last
            if await locator.is_visible(timeout=1000):
                return locator
        except Exception:
            continue
    return None


async def find_chat_input(page, config):
    for scope in all_scopes(page):
        locator = await find_chat_input_in_scope(scope, config)
        if locator is not None:
            return scope, locator
    return None, None


async def click_send_if_present(scope, config):
    pattern = text_regex(config["send_button_texts"])
    candidates = [
        scope.get_by_role("button", name=pattern),
        scope.locator("button").filter(has_text=pattern),
        scope.locator("[role='button']").filter(has_text=pattern)
    ]
    for locator in candidates:
        if await click_locator_if_visible(locator):
            return True
    return False


async def send_message(page, config, force=False):
    busy = await page_has_in_progress_text(page, config)
    if busy and not force and not config.get("send_when_busy"):
        log("İşlem devam ediyor görünüyor; mesaj gönderilmedi.")
        return False, "busy"

    scope, chat_input = await find_chat_input(page, config)
    if chat_input is None:
        log("Chat input bulunamadı.")
        return False, "input_missing"

    await chat_input.click()
    try:
        await chat_input.fill(config["message"])
    except Exception:
        await chat_input.press("Control+A")
        await chat_input.type(config["message"])

    sent = await click_send_if_present(scope, config)
    if not sent:
        await chat_input.press("Enter")

    log("Mesaj gönderildi.")
    return True, "sent"


async def main():
    config = load_config()
    assert_allowed_url(config["site_url"], config["allowed_hosts"])

    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            config["browser_profile_dir"],
            headless=config["headless"],
        )
        page = context.pages[0] if context.pages else await context.new_page()
        page.on("dialog", lambda dialog: asyncio.create_task(handle_dialog(dialog)))

        await page.goto(config["site_url"], wait_until="domcontentloaded", timeout=int(config["navigation_timeout_ms"]))

        log("Site watchdog başladı.")
        log("İlk çalıştırmada gerekiyorsa tarayıcıda manuel giriş yap.")

        last_send_at = 0.0
        last_signature = None
        same_signature_cycles = 0
        input_missing_cycles = 0
        consecutive_reloads = 0

        while True:
            try:
                if page.is_closed():
                    page = await recover_page(context, page, config, "page_closed", consecutive_reloads)
                    consecutive_reloads += 1

                assert_allowed_url(page.url, config["allowed_hosts"])

                responsive = await is_page_responsive(page, config)
                if not responsive and config.get("reload_when_page_frozen"):
                    page = await recover_page(context, page, config, "page_frozen", consecutive_reloads)
                    consecutive_reloads += 1
                    last_signature = None
                    same_signature_cycles = 0
                    input_missing_cycles = 0
                    continue

                approved = await click_approve_if_visible(page, config)
                if approved:
                    await asyncio.sleep(1)

                current_signature = await page_signature(page)
                if current_signature == last_signature:
                    same_signature_cycles += 1
                else:
                    same_signature_cycles = 0
                    last_signature = current_signature

                busy = await page_has_in_progress_text(page, config)
                _, chat_input = await find_chat_input(page, config)
                if chat_input is None:
                    input_missing_cycles += 1
                else:
                    input_missing_cycles = 0

                if input_missing_cycles >= int(config["input_missing_reload_cycles"]):
                    page = await recover_page(context, page, config, "chat_input_missing", consecutive_reloads)
                    consecutive_reloads += 1
                    input_missing_cycles = 0
                    last_signature = None
                    same_signature_cycles = 0
                    continue

                if busy and config.get("reload_when_stuck") and same_signature_cycles >= int(config["stuck_same_page_cycles"]):
                    page = await recover_page(context, page, config, "busy_same_screen_stuck", consecutive_reloads)
                    consecutive_reloads += 1
                    last_signature = None
                    same_signature_cycles = 0
                    input_missing_cycles = 0
                    await asyncio.sleep(2)
                    await click_approve_if_visible(page, config)
                    await send_message(page, config, force=True)
                    last_send_at = time.monotonic()
                    continue

                now = time.monotonic()
                should_send = (now - last_send_at) >= int(config["send_interval_seconds"])
                if should_send:
                    sent, status = await send_message(page, config)
                    if sent:
                        last_send_at = now
                        consecutive_reloads = 0
                    elif status == "input_missing":
                        input_missing_cycles += 1

                if not busy and chat_input is not None:
                    consecutive_reloads = 0

            except PlaywrightTimeoutError as e:
                log(f"Zaman aşımı: {e}")
                page = await recover_page(context, page, config, "playwright_timeout", consecutive_reloads)
                consecutive_reloads += 1
            except Exception as e:
                log(f"Hata: {e}")
                try:
                    page = await recover_page(context, page, config, "generic_error", consecutive_reloads)
                    consecutive_reloads += 1
                except Exception as recover_error:
                    log(f"Kurtarma da başarısız: {recover_error}")

            await asyncio.sleep(int(config["watch_interval_seconds"]))


if __name__ == "__main__":
    asyncio.run(main())
