import re
import os
import csv
import datetime
import subprocess
from bs4 import BeautifulSoup

from settings import (
    HEMNET_SEARCH_URL,
    LOCAL_HTML,
    CSV_FILE,
    PROPERTY_CARD_CLASS,
    COEFF_FLOOR,
    COEFF_PRICE,
    COEFF_ROOMS,
    COEFF_MONTHLY_FEE
)

WEEKDAY_MAP = {
    'Sön': 'Sun',
    'Mån': 'Mon',
    'Tis': 'Tue',
    'Ons': 'Wed',
    'Tor': 'Thu',
    'Fre': 'Fri',
    'Lör': 'Sat'
}
SWEDISH_WEEKDAYS = ['Mån', 'Tis', 'Ons', 'Tor', 'Fre', 'Lör', 'Sön']


def clean_text(text):
    if not text:
        return ''
    return text.replace('\xa0', ' ').replace('\n', ' ').strip()


def extract_number(text):
    if not text:
        return ''
    num = re.sub(r'[^\d,\.]', '', text).replace(',', '.')
    try:
        return str(float(num))
    except ValueError:
        return ''


def extract_int(text):
    if not text:
        return ''
    num = re.sub(r'[^\d]', '', text)
    return str(int(num)) if num else ''


def clean_rooms(text):
    return clean_text(text.replace('rum', '').replace(',', '.')).strip()


def clean_floor(text):
    return clean_text(text.replace('vån', '')).strip()


def clean_monthly_fee(text):
    return clean_text(text.replace('kr/mån', '').replace(' ', '')).strip()


def extract_viewing_and_time(a_tag):
    if not a_tag:
        return '', ''
    text = a_tag.get_text()
    pattern = r'(Sön|Mån|Tis|Ons|Tor|Fre|Lör|Idag)\s*(\d{1,2}\s+\w+)?\s*kl\s+\d{1,2}:\d{2}(?:-\d{1,2}:\d{2})?'
    match = re.search(pattern, text)
    if match:
        viewing_full = clean_text(match.group(0))
        # Extract view_time (the 'kl ...' part)
        time_match = re.search(r'kl\s+(\d{1,2}:\d{2}(?:-\d{1,2}:\d{2})?)', viewing_full)
        view_time = time_match.group(1) if time_match else ''
        # Remove 'kl ...' from viewing
        viewing = viewing_full.replace(time_match.group(0), '').strip() if time_match else viewing_full
        if viewing.startswith('Idag'):
            today = datetime.datetime.today()
            swe_weekday = SWEDISH_WEEKDAYS[today.weekday()]
            eng_weekday = WEEKDAY_MAP[swe_weekday]
            day = today.day
            month = today.strftime('%b').capitalize()
            viewing = re.sub(r'^Idag', f'{eng_weekday} {day} {month}', viewing)
        else:
            for swe, eng in WEEKDAY_MAP.items():
                if viewing.startswith(swe):
                    viewing = viewing.replace(swe, eng, 1)
                    break
        return viewing, view_time
    return '', ''


def extract_property_data(card):
    data = {}

    a_tag = card.find_parent('a')
    if a_tag and a_tag.has_attr('href'):
        href = a_tag['href']
        if href.startswith('http'):
            data['url'] = href
        else:
            data['url'] = 'https://www.hemnet.se' + href
        viewing, view_time = extract_viewing_and_time(a_tag)
        data['viewing'] = viewing
        data['view_time'] = view_time
    else:
        data['url'] = ''
        data['viewing'] = ''
        data['view_time'] = ''

    address = card.find('h2', class_='NestTitle_nestTitle__D7O_9')
    if address:
        address = address.find('div', class_='Header_truncate__ebq7a')
    data['address'] = clean_text(address.text if address else '')

    area = card.find('div', class_='Location_address___eOo4')
    if area:
        area = area.find('span')
    data['area'] = clean_text(area.text if area else '').replace(', Linköpings kommun', '')

    price = card.find('span', class_='ForSaleAttributes_askingPrice__ANshd')
    data['price'] = extract_int(price.text if price else '')

    attrs = card.find_all('div', class_='hcl-flex--item ForSaleAttributes_attribute__5Y0jr')
    living_area = rooms = floor = ''
    if len(attrs) >= 4:
        living_area = attrs[1].find('span').text if attrs[1].find('span') else ''
        rooms = attrs[2].find('span').text if attrs[2].find('span') else ''
        floor = attrs[3].find('span').text if attrs[3].find('span') else ''
    data['living_area'] = extract_number(living_area)
    data['rooms'] = clean_rooms(rooms)
    data['floor'] = clean_floor(floor)

    monthly_fee = price_per_m2 = ''
    if len(attrs) >= 6:
        monthly_fee = attrs[4].find('span').text if attrs[4].find('span') else ''
        price_per_m2 = attrs[5].find('span').text if attrs[5].find('span') else ''
    data['monthly_fee'] = clean_monthly_fee(monthly_fee)
    data['price_per_m2'] = extract_int(price_per_m2)

    features = []
    for tag in card.find_all('div', class_='NestDisplayTag_nestDisplayTagContainer__dfBQI'):
        features.append(clean_text(tag.text))
    data['features'] = ', '.join(features)

    agent = card.find('span', class_='NestBody_nestBody__B_PPT')
    data['agent'] = clean_text(agent.text if agent else '')

    return data


def parse_viewing_date(viewing):
    # Expects format like "Sun 7 Jul"
    try:
        parts = viewing.split()
        if len(parts) >= 3:
            day = int(parts[1])
            month = parts[2]
            # Use current year
            year = datetime.datetime.today().year
            # Parse month abbreviation
            date = datetime.datetime.strptime(f"{day} {month} {year}", "%d %b %Y")
            return date
    except Exception:
        pass
    return None


def parse_floor(floor_str):
    # Handles formats like "3/10", "11/11", "1", "3.5/4"
    if not floor_str:
        return -1
    match = re.match(r'(\d+(?:[.,]\d+)?)', floor_str)
    if match:
        try:
            return float(match.group(1).replace(',', '.'))
        except Exception:
            return -1
    return -1

def load_html():
    print(
        f"Open the URL {HEMNET_SEARCH_URL}\nin your browser, save the page as 'hemnet.html' in the project path ({os.getcwd()}), then press Enter to continue...")
    input()

    if not os.path.exists(LOCAL_HTML):
        print(f"File not found: {LOCAL_HTML}")
        return None

    with open(LOCAL_HTML, encoding='utf-8') as f:
        html_content = f.read()
    return html_content

def main():
    html_content = load_html()
    if html_content is None:
        return

    soup = BeautifulSoup(html_content, 'html.parser')
    cards = soup.find_all('div', class_=PROPERTY_CARD_CLASS)
    if not cards:
        print(f"No property cards found with class '{PROPERTY_CARD_CLASS}'.")
        return

    fieldnames = [
        'score', 'floor', 'viewing', 'view_time', 'address', 'area', 'price', 'living_area', 'rooms',
        'monthly_fee', 'price_per_m2', 'features', 'agent', 'url'
    ]

    all_rows = []
    for card in cards:
        data = extract_property_data(card)
        all_rows.append(data)

    def min_max(val, min_val, max_val):
        if max_val == min_val:
            return 0.5
        return (val - min_val) / (max_val - min_val)

    floors = [parse_floor(row['floor']) for row in all_rows if parse_floor(row['floor']) >= 0]
    prices = [float(row['price']) for row in all_rows if row['price']]
    monthly_fees = [float(row['monthly_fee'].replace(' ', '')) for row in all_rows if row['monthly_fee']]

    min_floor, max_floor = min(floors), max(floors)
    min_price, max_price = min(prices), max(prices)
    min_fee, max_fee = min(monthly_fees), max(monthly_fees)

    for row in all_rows:
        # Floor (higher is better)
        floor_val = parse_floor(row['floor'])
        norm_floor = min_max(floor_val, min_floor, max_floor) if floor_val >= 0 else 0
        # Price (lower is better)
        price_val = float(row['price']) if row['price'] else max_price
        norm_price = 1 - min_max(price_val, min_price, max_price)
        # Rooms (1.5 or 2 is best)
        try:
            rooms_val = float(row['rooms'])
        except Exception:
            rooms_val = 0
        norm_rooms = 1 if rooms_val in [1.5, 2] else 0
        # Monthly fee (lower is better)
        fee_val = float(row['monthly_fee'].replace(' ', '')) if row['monthly_fee'] else max_fee
        norm_fee = 1 - min_max(fee_val, min_fee, max_fee)
        # Weighted sum
        score = (
                        COEFF_FLOOR * norm_floor +
                        COEFF_PRICE * norm_price +
                        COEFF_ROOMS * norm_rooms +
                        COEFF_MONTHLY_FEE * norm_fee
                ) / (COEFF_FLOOR + COEFF_PRICE + COEFF_ROOMS + COEFF_MONTHLY_FEE)
        row['score'] = round(score, 3)

    rows_with_viewing = [row for row in all_rows if row['viewing']]
    rows_without_viewing = [row for row in all_rows if not row['viewing']]

    def sort_key(row):
        date = parse_viewing_date(row['viewing'])
        score = row.get('score', 0)
        return (date or datetime.datetime.max, -score)

    rows_with_viewing.sort(key=sort_key)
    ordered_rows = rows_with_viewing + rows_without_viewing

    # Filter out rows containing 'Nybyggnadsprojekt' in any field
    ordered_rows = [
        row for row in ordered_rows
        if all('Nybyggnadsprojekt' not in (str(value) or '') for value in row.values())
    ]

    with open(CSV_FILE, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for data in ordered_rows:
            writer.writerow(data)

    print(f"Saved {len(cards)} properties to {CSV_FILE}")

    # Open CSV with LibreOffice Calc
    subprocess.run(['libreoffice', '--calc', CSV_FILE])


if __name__ == '__main__':
    main()
