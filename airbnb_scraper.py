import re


def get_airbnb_price(page, url):

    page.goto(url)

    try:
        page.wait_for_selector("span:has-text('R$')", timeout=8000)
        page.wait_for_timeout(3000)  # deixa a página estabilizar
    except:
        pass

    text = page.inner_text("body")

    # pega valores com mais precisão (ex: R$ 355,80 ou R$ 1.234)
    matches = re.findall(r"R\$\s?[\d\.,]+", text)

    prices = []

    for m in matches:
        try:
            value = m.replace("R$", "").replace(".", "").replace(",", ".").strip()
            price = float(value)

            # 🔥 filtro essencial (ignora lixo tipo R$ 35, R$ 1, etc)
            if price >= 200:
                prices.append(price)

        except:
            continue

    if not prices:
        return None

    # pega o menor valor "válido"
    best_price = min(prices)

    return f"R${round(best_price, 2)}"