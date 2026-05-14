from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any

from .config import AppConfig, ProductRule


PRICE_PATTERNS = [
    re.compile(r"(?:💰|￥|¥)\s*(\d+(?:\.\d+)?)"),
    re.compile(r"(\d+(?:\.\d+)?)\s*(?:元|块|r|R)"),
    re.compile(r"(?<![A-Za-z0-9])(\d{2,5}(?:\.\d+)?)(?![A-Za-z0-9])"),
]


@dataclass
class RuleHit:
    chat: str
    sender: str
    time: str
    content: str
    matched_groups: list[str]
    matched_keywords: list[str]
    matched_products: list[str]
    prices: list[float]
    reason: str


def contains_any(text: str, words: list[str]) -> list[str]:
    lower = text.lower()
    return [word for word in words if word and word.lower() in lower]


def extract_prices(text: str) -> list[float]:
    prices: list[float] = []
    for pattern in PRICE_PATTERNS:
        for match in pattern.findall(text):
            try:
                price = float(match)
            except ValueError:
                continue
            if 0 < price < 100000:
                prices.append(price)
    return sorted(set(prices))


def product_matches(content: str, product: ProductRule, prices: list[float]) -> tuple[bool, str | None]:
    keyword_hits = contains_any(content, product.keywords)
    if not keyword_hits:
        return False, None
    if product.max_price is None:
        return True, f"{product.name} 命中关键词：{', '.join(keyword_hits)}"
    if not prices:
        return True, f"{product.name} 命中关键词但未识别价格，建议人工确认"
    valid_prices = [price for price in prices if price <= product.max_price]
    if valid_prices:
        return True, f"{product.name} 价格 {min(valid_prices):g} <= 阈值 {product.max_price:g}"
    return False, None


def evaluate_message(item: dict[str, Any], config: AppConfig) -> RuleHit | None:
    chat = str(item.get("chat", ""))
    content = str(item.get("content", ""))
    sender = str(item.get("sender", ""))
    matched_groups = contains_any(chat, config.target_groups)
    if not matched_groups:
        return None

    blacklist_hits = contains_any(content, config.blacklist_words)
    if blacklist_hits:
        return None

    prices = extract_prices(content)
    keyword_hits = contains_any(content, config.global_keywords)
    product_names: list[str] = []
    reasons: list[str] = []

    for product in config.products:
        ok, reason = product_matches(content, product, prices)
        if ok:
            product_names.append(product.name)
            if reason:
                reasons.append(reason)

    if not keyword_hits and not product_names:
        return None

    if keyword_hits:
        reasons.insert(0, f"全局关键词：{', '.join(keyword_hits)}")

    return RuleHit(
        chat=chat,
        sender=sender,
        time=str(item.get("time", "")),
        content=content,
        matched_groups=matched_groups,
        matched_keywords=keyword_hits,
        matched_products=product_names,
        prices=prices,
        reason="；".join(reasons),
    )

