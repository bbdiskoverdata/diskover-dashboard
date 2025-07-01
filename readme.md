# Diskover Index Dashboard

Diskover Index Dashboard is an interactive Streamlit application for visualizing and reporting on file storage metrics across multiple indexes. Upload a CSV export from Diskover and explore your data in a dark-themed dashboard, complete with charts and PDF reporting.

## Features

- **Index filtering**: Select one or more indexes (or view all) to focus your analysis.
- **Unit toggle**: Switch between GB, TB, and PB for all size metrics.
- **Extensions summary**:
  - Bar chart of the top 20 file extensions by total size.
  - Pie chart of file extensions by count.
- **Hot/Warm/Cold summary**:
  - Bar charts comparing size and count across storage tiers (Hot, Warm, Cold) for both MTime and ATime fields.
- **Largest files table**: Interactive table listing the top 50 largest files, with columns for file name, extension, size, and last modified timestamp (in your local timezone).
- **PDF report**: Generate and download a PDF report containing all charts and the largest files table.

## Requirements

- Python 3.7+
- streamlit
- pandas
- plotly
- fpdf
- pillow

Install dependencies:

```bash
pip install streamlit pandas plotly fpdf pillow
```

## Usage

1. Clone or download this repository.
2. Place `Diskover_Dashboard_App.py` (and optionally `Diskover_Banner.png`) in your project folder.
3. Run the app:
   ```bash
   streamlit run Diskover_Dashboard_App.py
   ```
4. Open `http://localhost:8501` in your browser.
5. Upload your CSV file exported from Diskover.
6. Use the controls to filter indexes, change size units, and explore summaries.
7. Click "📄 Generate PDF Report" to produce a downloadable PDF.
8. (Optional) Click "❌ Close App" to exit the application.

## CSV Format

Your CSV file must contain the following columns:

- `Index`: Name of the index.
- `Type`: Row type, e.g., "Top Extension", "Largest File", "Hot Summary", etc.
- `Key`: The key or identifier (e.g., extension name or file name).
- `Count`: Number of occurrences.
- `Size (Bytes)`: Total size in bytes.
- `MTime`: Last modification timestamp (ISO format).
- `ATime`: Last access timestamp (ISO format).

Ensure that summary rows for Hot/Warm/Cold use `Type` values containing "Summary".

## Customization

- **Styling**: Modify the CSS block at the top of the script to change colors or fonts.
- **Page settings**: Adjust `st.set_page_config` parameters for page title, layout, and icon.
- **Logo**: Replace `Diskover_Banner.png` with your own image; update the `Image.open` path if needed.

## Contributing

Feel free to submit issues or pull requests to improve functionality, add new charts, or enhance styling.

## License

This project is licensed under the MIT License. Feel free to use and modify it as needed.

