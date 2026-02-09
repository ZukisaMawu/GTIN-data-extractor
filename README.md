# 📦 GTIN Data Extractor

A powerful web application for extracting and combining GTIN data from multiple JSON files into a single Excel file with automatic translation support.

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://your-app-url.streamlit.app)

## ✨ Features

- 📁 **Drag & Drop Interface** - Easy file upload with multiple file support
- 🔄 **Batch Processing** - Process multiple JSON files simultaneously
- 🌐 **Auto Translation** - Automatically detects and translates non-English text to English
- 📊 **Data Preview** - View extracted data before downloading
- 📈 **Real-time Statistics** - See record counts, status breakdown, and translation stats
- 💾 **Excel Export** - Download combined data as a professionally formatted Excel file
- ⚡ **Fast Processing** - Parallel processing with configurable workers

## 🚀 Quick Start

### Option 1: Use the Deployed App (Easiest)
Just visit: [https://your-app-url.streamlit.app](https://your-app-url.streamlit.app)

### Option 2: Run Locally

1. **Clone this repository**:
   ```bash
   git clone https://github.com/YOUR_USERNAME/gtin-data-extractor.git
   cd gtin-data-extractor
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the app**:
   ```bash
   streamlit run gtin_streamlit_app.py
   ```

4. **Open your browser** at `http://localhost:8501`

## 📖 How to Use

1. **Upload JSON files** - Drag and drop or browse for your JSON files
2. **Configure settings** (optional):
   - Enable/disable translation
   - Adjust translation workers for speed (1-10)
3. **Process files** - Click the "Process Files" button
4. **Review results** - Check the statistics and preview
5. **Download** - Click the download button to get your Excel file

## 📊 Output Format

The Excel file contains the following columns:
- **Source_File** - Original JSON filename
- **GTIN** - Global Trade Item Number
- **Record_Status** - Status (ACTIVE, ERROR, etc.)
- **Brand_Name** - Brand name (translated if enabled)
- **Product_Description** - Product description (translated if enabled)
- **License_Name** - License holder name (translated if enabled)
- **License_Key** - License identifier
- **License_Type** - Type of license
- **Licensee_GLN** - Global Location Number
- **Address fields** - Street, City, Suburb, Postal Code, Country Code
- **Net_Content** - Product net content with units
- **Is_Complete** - Completeness indicator
- **Error_Code** - Error code (if applicable)
- **Error_Message** - Detailed error message (if applicable)

### Translation Columns (when enabled)
- `Brand_Name_Language` - Detected language code
- `Brand_Name_Original` - Original text before translation
- Same pattern for `Product_Description` and `License_Name`

## ⚙️ Settings

### Translation
- **Enable Translation**: Automatically translates Brand Name, Product Description, and License Name from other languages to English
- **Translation Workers**: Controls parallel processing (1-10)
  - Lower (1-3): Less resource intensive, slower
  - Higher (5-10): Faster processing, more resource intensive

## 🛠️ Technical Details

Built with:
- **Streamlit** - Web framework
- **Pandas** - Data processing
- **deep-translator** - Language translation
- **langdetect** - Language detection
- **openpyxl** - Excel file generation

## 📝 Requirements

- Python 3.8 or higher
- Internet connection (for translation feature)

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is open source and available under the MIT License.

## 🐛 Troubleshooting

### App won't start
- Ensure all dependencies are installed: `pip install -r requirements.txt`
- Check Python version: `python --version` (should be 3.8+)

### Translation errors
- Reduce the number of translation workers
- Check your internet connection (translation requires API access)

### File processing errors
- Ensure JSON files are properly formatted
- Verify files contain the expected GTIN data structure

## 💡 Performance Tips

- **Large batches**: Increase translation workers (5-10) for faster processing
- **Limited resources**: Decrease translation workers (1-3) to reduce memory usage
- **No translation needed**: Disable translation for fastest processing

## 📞 Support

For issues or questions:
- Open an [issue](https://github.com/YOUR_USERNAME/gtin-data-extractor/issues)
- Check existing issues for solutions

---

**Made with ❤️ using Streamlit**

---

**Made with ❤️ using Streamlit**
