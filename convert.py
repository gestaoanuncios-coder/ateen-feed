"""Converte o feed XML da VTEX (padrao Google/Meta) em CSV no padrao OpenAI Ads."""
import csv
import html
import re
import json
import urllib.request
import xml.etree.ElementTree as ET

FEED_URL = "https://www.ateen.com.br/XMLData/facebook-catalogo.xml"
OUTPUT = "docs/ateen-openai.csv"

SELLER_NAME = "ATEEN"
SELLER_URL = "https://www.ateen.com.br"
RETURN_POLICY = "https://ateen.zendesk.com/hc/pt-br/sections/360003548834-Troca-e-Devolu%C3%A7%C3%A3o"
COUNTRY = "BR"
CURRENCY = "BRL"

# ID da colecao New In na VTEX (Catalogo > Colecoes). Produtos dela recebem custom_label_0 = new_in
NEW_IN_COLLECTION = "1745"

AVAILABILITY = {
    "in stock": "in_stock", "in_stock": "in_stock",
    "out of stock": "out_of_stock", "out_of_stock": "out_of_stock",
    "preorder": "pre_order", "pre_order": "pre_order",
    "backorder": "backorder",
}

COLUMNS = [
    "item_id", "group_id", "title", "description", "url", "brand", "image_url",
    "additional_image_urls", "price", "sale_price", "availability", "condition",
    "product_type", "google_product_category", "color", "size", "gender", "age_group",
    "custom_label_0", "custom_label_1", "custom_label_2", "custom_label_3", "custom_label_4",
    "seller_name", "seller_url", "return_policy", "target_countries", "store_country",
    "is_eligible_search", "is_eligible_checkout", "is_ads_eligible",
]


def local(tag):
    return tag.split("}")[-1].lower()


def clean(text):
    if not text:
        return ""
    text = html.unescape(text)
    text = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def fmt_price(value):
    if not value:
        return ""
    num = re.search(r"[\d.,]+", value)
    if not num:
        return ""
    n = num.group(0)
    if "," in n and "." in n:
        n = n.replace(".", "").replace(",", ".")
    elif "," in n:
        n = n.replace(",", ".")
    try:
        return f"{float(n):.2f} {CURRENCY}"
    except ValueError:
        return ""


def new_in_ids():
    """Busca na API publica da VTEX os produtos da colecao New In."""
    if not NEW_IN_COLLECTION.isdigit():
        return set()
    ids, start = set(), 0
    while start < 2500:
        url = (f"{SELLER_URL}/api/catalog_system/pub/products/search"
               f"?fq=productClusterIds:{NEW_IN_COLLECTION}&_from={start}&_to={start + 49}")
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        batch = json.loads(urllib.request.urlopen(req, timeout=60).read())
        if not batch:
            break
        for prod in batch:
            ids.add(str(prod.get("productId", "")))
            for sku in prod.get("items", []):
                ids.add(str(sku.get("itemId", "")))
        start += 50
    print(f"{len(ids)} IDs na colecao New In")
    return ids


def main():
    new_in = new_in_ids()
    req = urllib.request.Request(FEED_URL, headers={"User-Agent": "Mozilla/5.0"})
    data = urllib.request.urlopen(req, timeout=120).read()
    root = ET.fromstring(data)

    items = [el for el in root.iter() if local(el.tag) in ("item", "entry")]
    rows = []
    for item in items:
        f, extra_imgs = {}, []
        for child in item:
            name = local(child.tag)
            value = (child.text or "").strip()
            if name == "additional_image_link":
                extra_imgs.append(value)
            elif name not in f:
                f[name] = value

        item_id = f.get("id", "")
        link = f.get("link", "")
        if not item_id or not link:
            continue

        price = fmt_price(f.get("price"))
        sale = fmt_price(f.get("sale_price"))
        if not price and sale:
            price, sale = sale, ""

        rows.append({
            "item_id": item_id,
            "group_id": f.get("item_group_id", ""),
            "title": clean(f.get("title"))[:150],
            "description": clean(f.get("description"))[:5000],
            "url": link,
            "brand": clean(f.get("brand")) or SELLER_NAME,
            "image_url": f.get("image_link", ""),
            "additional_image_urls": ",".join(extra_imgs[:10]),
            "price": price,
            "sale_price": sale if sale and sale != price else "",
            "availability": AVAILABILITY.get(f.get("availability", "").lower(), "in_stock"),
            "condition": f.get("condition", "new") or "new",
            "product_type": clean(f.get("product_type")),
            "google_product_category": clean(f.get("google_product_category")),
            "color": clean(f.get("color")),
            "size": clean(f.get("size")),
            "gender": f.get("gender", ""),
            "age_group": f.get("age_group", ""),
            **{f"custom_label_{i}": clean(f.get(f"custom_label_{i}")) for i in range(5)},
            "custom_label_0": "new_in" if item_id in new_in else clean(f.get("custom_label_0")),
            "seller_name": SELLER_NAME,
            "seller_url": SELLER_URL,
            "return_policy": RETURN_POLICY,
            "target_countries": COUNTRY,
            "store_country": COUNTRY,
            "is_eligible_search": "true",
            "is_eligible_checkout": "false",
            "is_ads_eligible": "true",
        })

    with open(OUTPUT, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
    print(f"{len(rows)} produtos exportados para {OUTPUT}")


if __name__ == "__main__":
    main()
