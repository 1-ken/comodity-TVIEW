#!/usr/bin/env python3
"""
Utility script to extract all trading pairs from the TradingView-like HTML structure.
This demonstrates how the new scraper extracts pairs dynamically.
"""
import json
import re
from bs4 import BeautifulSoup

from app.core.paths import EXTRACTED_PAIRS_PATH, EXTRACT_PAIRS_HTML_PATH


def extract_pairs_from_html(html_file: str) -> dict:
    """
    Extract all trading pairs and prices from the HTML file.
    Organizes pairs by their category sections.

    Returns a dictionary with pairs organized by category:
    {
        "Indices": [{"pair": "SPX", "price": "6,952.59"}, ...],
        "Stocks": [...],
        "Futures": [...],
        "Forex": [...],
        "Crypto": [...]
    }
    """
    with open(html_file, "r", encoding="utf-8") as f:
        html_content = f.read()

    soup = BeautifulSoup(html_content, "html.parser")

    categories = {}
    current_category = "General"

    # Find all wrapper elements that contain pairs
    all_wrappers = soup.find_all(class_="wrap-IEe5qpW4")

    for wrapper in all_wrappers:
        # Check if this wrapper is a category separator
        separator = wrapper.find(class_="separator-eCC6Skn5")
        if separator:
            label_elem = separator.find(class_="label-eCC6Skn5")
            if label_elem:
                current_category = label_elem.get_text(strip=True)
                categories[current_category] = []
                continue

        # This is a pair element
        symbol_elem = wrapper.find(class_="symbol-RsFlttSS")
        if symbol_elem:
            try:
                # Ensure category exists
                if current_category not in categories:
                    categories[current_category] = []

                # Get pair name
                name_elem = symbol_elem.find(class_="symbolNameText-RsFlttSS")
                if not name_elem:
                    continue

                pair = name_elem.get_text(strip=True)
                if not pair:
                    continue

                # Get price from the last price cell
                price_elem = symbol_elem.find(class_="last-RsFlttSS")
                if price_elem:
                    inner_elem = price_elem.find(class_="inner-RsFlttSS")
                    if inner_elem:
                        price = inner_elem.get_text()
                        # Clean up price - remove extra whitespace but keep formatting
                        price = re.sub(r"\s+", "", price).strip()
                    else:
                        price = "N/A"
                else:
                    price = "N/A"

                categories[current_category].append({
                    "pair": pair,
                    "price": price,
                })

            except Exception as e:
                print(f"Error extracting pair: {e}")
                continue

    return categories


def main():
    html_file = EXTRACT_PAIRS_HTML_PATH

    if not html_file.exists():
        print(f"Error: {html_file} not found")
        return

    print(f"Extracting pairs from {html_file}...")
    pairs_data = extract_pairs_from_html(str(html_file))

    # Print results
    total_pairs = sum(len(v) for v in pairs_data.values())
    print(f"\n✓ Successfully extracted {total_pairs} pairs from {len(pairs_data)} categories\n")

    for category, pairs in pairs_data.items():
        if pairs:  # Only show categories that have pairs
            print(f"\n📊 {category} ({len(pairs)} pairs):")
            print("-" * 70)
            for i, pair_data in enumerate(pairs, 1):
                print(f"  {i:2}. {pair_data['pair']:12} → {pair_data['price']:20}")

    # Save to JSON
    with open(EXTRACTED_PAIRS_PATH, "w") as f:
        json.dump(pairs_data, f, indent=2)
    print(f"\n✓ Extracted data saved to {EXTRACTED_PAIRS_PATH}")

    # Print summary statistics
    print("\n📈 Summary:")
    print("-" * 70)
    for category, pairs in pairs_data.items():
        if pairs:
            print(f"  {category:15} {len(pairs):3} pairs")


if __name__ == "__main__":
    main()
