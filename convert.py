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

# True = o feed so leva produtos New In. False = catalogo inteiro
ONLY_NEW_IN = True

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
