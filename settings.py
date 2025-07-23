# Hemnet search URL with filters
HEMNET_SEARCH_URL = "https://www.hemnet.se/bostader?elevator=1&balcony=1&price_max=2000000&price_min=1600000&living_area_min=35&item_types[]=bostadsratt&location_ids[]=17847"

# File paths
LOCAL_HTML = 'hemnet.html'
CSV_FILE = 'hemnet_properties.csv'

# HTML selectors
PROPERTY_CARD_CLASS = 'Content_content__lg290'

# Scoring coefficients
COEFF_FLOOR = 3
COEFF_PRICE = 2
COEFF_ROOMS = 1
COEFF_MONTHLY_FEE = 3
