import streamlit as st
import json
import pandas as pd
from pathlib import Path
from typing import List
from deep_translator import GoogleTranslator
from langdetect import detect
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import io

# Set page config
st.set_page_config(
    page_title="GTIN Data Extractor",
    page_icon="📦",
    layout="wide"
)

def extract_gtin_data_from_file(json_content, filename):
    """Extract GTIN data from JSON content."""
    try:
        data = json.loads(json_content)
        records = []
        
        for item in data:
            record = {
                'Source_File': filename,
                'GTIN': None,
                'Record_Status': None,
                'Brand_Name': None,
                'Product_Description': None,
                'License_Name': None,
                'License_Key': None,
                'License_Type': None,
                'Licensee_GLN': None,
                'Street_Address': None,
                'Address_Line_2': None,
                'Address_Line_3': None,
                'City': None,
                'Suburb': None,
                'Postal_Code': None,
                'Country_Code': None,
                'Net_Content': None,
                'Is_Complete': None,
                'Error_Code': None,
                'Error_Message': None
            }
            
            record['GTIN'] = item.get('gtin', 'N/A')
            
            if 'code' in item and 'validationErrors' in item:
                record['Record_Status'] = 'ERROR'
                record['Error_Code'] = item.get('code', 'N/A')
                
                validation_errors = item.get('validationErrors', [])
                error_messages = []
                for error in validation_errors:
                    for err in error.get('errors', []):
                        error_messages.append(f"{err.get('errorCode', '')}: {err.get('message', '')}")
                
                record['Error_Message'] = ' | '.join(error_messages) if error_messages else 'N/A'
            
            elif 'gtinRecordStatus' in item:
                record['Record_Status'] = item.get('gtinRecordStatus', 'N/A')
                record['Is_Complete'] = item.get('isComplete', 'N/A')
                
                brand_name = item.get('brandName', [])
                if brand_name and isinstance(brand_name, list) and len(brand_name) > 0:
                    record['Brand_Name'] = brand_name[0].get('value', 'N/A')
                
                product_desc = item.get('productDescription', [])
                if product_desc and isinstance(product_desc, list) and len(product_desc) > 0:
                    record['Product_Description'] = product_desc[0].get('value', 'N/A')
                
                net_content = item.get('netContent', [])
                if net_content and isinstance(net_content, list) and len(net_content) > 0:
                    content_value = net_content[0].get('value', '')
                    content_unit = net_content[0].get('unitCode', '')
                    if content_value and content_unit:
                        record['Net_Content'] = f"{content_value} {content_unit}"
                    elif content_value:
                        record['Net_Content'] = content_value
                
                gs1_licence = item.get('gs1Licence', {})
                if gs1_licence:
                    record['License_Name'] = gs1_licence.get('licenseeName', 'N/A')
                    record['License_Key'] = gs1_licence.get('licenceKey', 'N/A')
                    record['License_Type'] = gs1_licence.get('licenceType', 'N/A')
                    record['Licensee_GLN'] = gs1_licence.get('licenseeGLN', 'N/A')
                    
                    address = gs1_licence.get('address', {})
                    if address:
                        street_addr = address.get('streetAddress', {})
                        record['Street_Address'] = street_addr.get('value', 'N/A') if isinstance(street_addr, dict) else 'N/A'
                        
                        addr_line2 = address.get('streetAddressLine2', {})
                        record['Address_Line_2'] = addr_line2.get('value', 'N/A') if isinstance(addr_line2, dict) else 'N/A'
                        
                        addr_line3 = address.get('streetAddressLine3', {})
                        record['Address_Line_3'] = addr_line3.get('value', 'N/A') if isinstance(addr_line3, dict) else 'N/A'
                        
                        locality = address.get('addressLocality', {})
                        record['City'] = locality.get('value', 'N/A') if isinstance(locality, dict) else 'N/A'
                        
                        suburb = address.get('addressSuburb', {})
                        record['Suburb'] = suburb.get('value', 'N/A') if isinstance(suburb, dict) else 'N/A'
                        
                        record['Postal_Code'] = address.get('postalCode', 'N/A')
                        record['Country_Code'] = address.get('countryCode', 'N/A')
            
            records.append(record)
        
        return records
    
    except Exception as e:
        st.error(f"Error processing {filename}: {str(e)}")
        return []

def add_translation_columns(df, fields_to_translate=['Brand_Name', 'Product_Description', 'License_Name']):
    """Add translation columns and detect which records need translation."""
    needs_translation = set()
    
    for field in fields_to_translate:
        if field in df.columns:
            df[f'{field}_Language'] = None
            df[f'{field}_Original'] = None
            df[f'{field}_Translation_Status'] = 'Not Needed'  # Track translation status
    
    for field in fields_to_translate:
        if field not in df.columns:
            continue
        
        for idx, value in df[field].items():
            if value and value != 'N/A' and isinstance(value, str) and len(value.strip()) > 0:
                try:
                    lang = detect(value)
                    df.at[idx, f'{field}_Language'] = lang
                    
                    if lang != 'en':
                        needs_translation.add((idx, field, value, lang))
                        df.at[idx, f'{field}_Translation_Status'] = 'Pending'
                except:
                    df.at[idx, f'{field}_Language'] = None
                    df.at[idx, f'{field}_Translation_Status'] = 'Detection Failed'
    
    return df, needs_translation

def translate_batch(df, needs_translation, max_workers=3, progress_bar=None):
    """Translate records using parallel processing with verification."""
    if not needs_translation:
        return df
    
    def translate_item(item):
        idx, field, text, lang = item
        try:
            time.sleep(0.05)
            translated = GoogleTranslator(source=lang, target='en').translate(text)
            
            # Verify the translation actually worked
            if translated and translated != text:
                try:
                    # Check if translated text is actually in English
                    translated_lang = detect(translated)
                    if translated_lang == 'en':
                        return (idx, field, text, translated, 'Success')
                    else:
                        # Translation produced non-English text
                        return (idx, field, text, None, 'Failed - Still Non-English')
                except:
                    # Can't detect language of translation, assume it worked
                    return (idx, field, text, translated, 'Success')
            else:
                # Translation returned same text or empty
                return (idx, field, text, None, 'Failed - No Translation')
                
        except Exception as e:
            return (idx, field, text, None, f'Failed - Error: {str(e)}')
    
    completed = 0
    total = len(needs_translation)
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(translate_item, item): item for item in needs_translation}
        
        for future in as_completed(futures):
            idx, field, original, translated, status = future.result()
            
            if status == 'Success' and translated:
                df.at[idx, f'{field}_Original'] = original
                df.at[idx, field] = translated
                df.at[idx, f'{field}_Translation_Status'] = 'Success'
            else:
                # Translation failed - mark the field
                df.at[idx, f'{field}_Translation_Status'] = status
                df.at[idx, field] = 'Translation Failed'
            
            completed += 1
            if progress_bar:
                progress_bar.progress(completed / total)
    
    return df

def clean_untranslatable_records(df, critical_fields=['Brand_Name', 'Product_Description', 'License_Name']):
    """Remove records where critical fields failed translation."""
    initial_count = len(df)
    rows_to_drop = []
    
    for idx, row in df.iterrows():
        should_drop = False
        
        for field in critical_fields:
            status_col = f'{field}_Translation_Status'
            
            # Check if field exists and has translation status
            if status_col in df.columns:
                status = row[status_col]
                field_value = row[field]
                
                # Drop if:
                # 1. Translation failed AND field had actual content (not N/A or empty)
                # 2. Field shows "Translation Failed" message
                if (status and status.startswith('Failed')) or (field_value == 'Translation Failed'):
                    # Only drop if the original field had content
                    original_col = f'{field}_Original'
                    if original_col in df.columns and pd.notna(row[original_col]):
                        should_drop = True
                        break
        
        if should_drop:
            rows_to_drop.append(idx)
    
    if rows_to_drop:
        df = df.drop(rows_to_drop)
        removed_count = len(rows_to_drop)
        st.warning(f"Removed {removed_count} records with untranslatable content (kept {len(df)} valid records)")
    
    return df

def prepare_output_dataframe(df):
    """Prepare clean output with only specified columns."""
    output_columns = ['GTIN', 'Record_Status', 'Brand_Name', 'Product_Description', 'License_Name', 'Error_Message']
    
    # Select only the columns that exist in the dataframe
    available_columns = [col for col in output_columns if col in df.columns]
    
    # Create clean output dataframe
    output_df = df[available_columns].copy()
    
    return output_df

def process_files(uploaded_files, enable_translation=True, translation_workers=3):
    """Process uploaded JSON files."""
    all_records = []
    successful_files = 0
    
    # Phase 1: Extraction
    progress_text = st.empty()
    progress_bar = st.progress(0)
    
    for i, uploaded_file in enumerate(uploaded_files):
        progress_text.text(f"Extracting data from {uploaded_file.name} ({i+1}/{len(uploaded_files)})...")
        progress_bar.progress((i + 1) / len(uploaded_files))
        
        content = uploaded_file.read().decode('utf-8')
        records = extract_gtin_data_from_file(content, uploaded_file.name)
        
        if records:
            all_records.extend(records)
            successful_files += 1
    
    progress_text.text(f"✓ Extracted {len(all_records)} records from {successful_files} files")
    
    if not all_records:
        return None
    
    df = pd.DataFrame(all_records)
    
    # Phase 2: Translation
    if enable_translation:
        progress_text.text("Detecting languages...")
        df, needs_translation = add_translation_columns(df)
        
        if needs_translation:
            progress_text.text(f"Translating {len(needs_translation)} fields...")
            translation_progress = st.progress(0)
            df = translate_batch(df, needs_translation, max_workers=translation_workers, progress_bar=translation_progress)
            progress_text.text(f"✓ Translation complete!")
            
            # Phase 3: Clean up untranslatable records
            progress_text.text("Removing untranslatable records...")
            df = clean_untranslatable_records(df)
        else:
            progress_text.text("✓ No translation needed - all text is in English!")
    
    progress_bar.empty()
    
    # Prepare clean output
    output_df = prepare_output_dataframe(df)
    
    return output_df, df  # Return both clean output and full data for statistics

# Streamlit App UI
st.title("GTIN Data Extractor")
st.markdown("Upload JSON files to extract and combine data into an Excel file")

# Sidebar settings
st.sidebar.header("Settings")
enable_translation = st.sidebar.checkbox("Enable Translation", value=True, 
    help="Translate non-English text in Brand Name, Product Description, and License Name")
translation_workers = st.sidebar.slider("Translation Workers", min_value=1, max_value=10, value=3,
    help="Number of parallel translation threads (higher = faster but more resource intensive)")

# File uploader
uploaded_files = st.file_uploader(
    "Upload JSON files",
    type=['json'],
    accept_multiple_files=True,
    help="Drag and drop multiple JSON files here"
)

if uploaded_files:
    st.success(f"✓ {len(uploaded_files)} file(s) uploaded")
    
    # Show file names
    with st.expander("View uploaded files"):
        for file in uploaded_files:
            st.text(f"• {file.name}")
    
    # Process button
    if st.button("Process Files", type="primary"):
        with st.spinner("Processing..."):
            result = process_files(uploaded_files, enable_translation, translation_workers)
            
            if result is not None:
                output_df, full_df = result
                st.success("✓ Processing complete!")
                
                # Summary statistics
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Total Records", len(output_df))
                
                with col2:
                    if 'Record_Status' in output_df.columns:
                        active_count = len(output_df[output_df['Record_Status'] == 'ACTIVE'])
                        st.metric("Active Records", active_count)
                
                with col3:
                    if 'Record_Status' in output_df.columns:
                        error_count = len(output_df[output_df['Record_Status'] == 'ERROR'])
                        st.metric("Error Records", error_count)
                
                # Status breakdown
                if 'Record_Status' in output_df.columns:
                    st.subheader("Record Status Breakdown")
                    status_counts = output_df['Record_Status'].value_counts()
                    st.bar_chart(status_counts)
                
                # Translation statistics
                if enable_translation:
                    st.subheader("Translation Statistics")
                    translation_stats = []
                    
                    for field in ['Brand_Name', 'Product_Description', 'License_Name']:
                        status_col = f'{field}_Translation_Status'
                        if status_col in full_df.columns:
                            success = len(full_df[full_df[status_col] == 'Success'])
                            failed = len(full_df[full_df[status_col].str.startswith('Failed', na=False)])
                            
                            if success > 0:
                                translation_stats.append(f"✓ {field}: {success} successful translations")
                            if failed > 0:
                                translation_stats.append(f"✗ {field}: {failed} failed translations (removed)")
                    
                    if translation_stats:
                        for stat in translation_stats:
                            st.text(stat)
                    else:
                        st.text("✓ No translations needed - all text was in English")
                
                # Preview data
                st.subheader("Data Preview (Clean Output)")
                st.dataframe(output_df.head(10), use_container_width=True)
                
                # Download button
                st.subheader("Download Results")
                
                # Create Excel file in memory
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    output_df.to_excel(writer, index=False, sheet_name='GTIN Data')
                
                excel_data = output.getvalue()
                
                st.download_button(
                    label="Download Excel File",
                    data=excel_data,
                    file_name="gtin_combined_output.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            else:
                st.error("Failed to process files. Please check the file format.")

else:
    st.info("Upload JSON files to get started")
    
    # Instructions
    st.markdown("""
    ### How to use:
    1. **Upload** your JSON files using the file uploader above
    2. **Configure** translation settings in the sidebar (optional)
    3. **Click** the "Process Files" button
    4. **Download** the generated Excel file
    
    


