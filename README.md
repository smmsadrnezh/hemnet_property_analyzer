# Hemnet Property Analyzer

Hemnet Property Analyzer is a Python-based tool designed to scrape property listings from Hemnet.se search results, analyze the data, and score properties based on customizable criteria such as floor level, price, number of rooms, and monthly fees. The tool helps users identify the best properties according to their preferences.

## Features
- Scrapes property data from a saved HTML file of Hemnet search results.
- Normalizes and scores properties based on user-defined coefficients.
- Sorts properties based on their calculated scores for easier comparison.
- Outputs the analyzed data to a CSV file for further review.

## Requirements
- Python 3.10 or higher
- Required Python packages (listed in `requirements.txt`)

## Installation
1. Clone this repository to your local machine:
   ```bash
   git clone <repository-url>
   cd hemnet_property_analyzer
   ```

2. Create a virtual environment and activate it:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage
1. Run the program by executing the following command:
   ```bash
   python main.py
   ```
2. Follow the on-screen instructions to process the data. You will be prompted to open Hemnet in your browser, perform a search with your desired filters, and save the search results page as `hemnet.html` in the project directory.
3. The analyzed data will be saved to `hemnet_properties.csv` in the project directory. Open this file in LibreOffice Calc or any spreadsheet software for further analysis.

## Configuration
You can customize the tool's behavior by modifying the `settings.py` file. Key settings include:
- `HEMNET_SEARCH_URL`: The URL used for Hemnet searches.
- `COEFF_FLOOR`, `COEFF_PRICE`, `COEFF_ROOMS`, `COEFF_MONTHLY_FEE`: Coefficients for scoring properties.

## Output
The program generates a CSV file (`hemnet_properties.csv`) containing the scraped and analyzed property data, including scores for each property.

## License
This project is licensed under the MIT License.

## Contributing
Contributions are welcome! Feel free to submit issues or pull requests to improve the tool.
