from playwright.sync_api import sync_playwright
import re


def get_airbnb_price(page, url):

    page.goto(url)

    try:
        page.wait_for_selector("span:has-text('R$')", timeout=8000)
    except:
        pass

    text = page.inner_text("body")

    matches = re.findall(r"R\$\s?\d+", text)

    if matches:
        return matches[0]

    return None