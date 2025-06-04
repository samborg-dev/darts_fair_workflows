from instrument_data_parser_oo import InstrumentDataParser
import os
import pandas as pd
import numpy as np
import warnings
from datetime import datetime

# Suppress the specific datetime parsing warning
warnings.filterwarnings('ignore', category=UserWarning, module='pandas')

# Set pandas display options for better viewing in IDE
pd.set_option('display.max_columns', None)  # Show all columns
pd.set_option('display.width', None)        # Auto-detect display width
pd.set_option('display.max_rows', 50)       # Show first 50 rows
pd.set_option('display.max_colwidth', 30)   # Limit column width
pd.set_option('display.expand_frame_repr', False)  # Don't wrap wide tables

def parse_date(date_str):
    """Parse date string with multiple format attempts"""
    if pd.isna(date_str) or not isinstance(date_str, str):
        return pd.NaT
    
    # Common date formats in the data
    date_formats = [
        '%Y%m%d',           # 20240315
        '%Y-%m-%d',         # 2024-03-15
        '%d/%m/%Y',         # 15/03/2024
        '%m/%d/%Y',         # 03/15/2024
        '%Y%m%d %H:%M:%S',  # 20240315 14:30:00
        '%Y-%m-%d %H:%M:%S' # 2024-03-15 14:30:00
    ]
    
    for fmt in date_formats:
        try:
            return datetime.strptime(date_str.strip(), fmt)
        except ValueError:
            continue
    
    return pd.NaT

def format_dataframe(df):
    """Format the DataFrame for better display"""
    # Create a copy to avoid modifying the original
    formatted_df = df.copy()
    
    # Format numeric columns
    numeric_cols = formatted_df.select_dtypes(include=[np.number]).columns
    for col in numeric_cols:
        if 'array' not in col.lower():  # Don't format array columns
            formatted_df[col] = formatted_df[col].apply(lambda x: f"{x:.3f}" if pd.notnull(x) else x)
    
    # Format datetime columns if they exist
    date_cols = [col for col in formatted_df.columns if 'date' in col.lower() or 'time' in col.lower()]
    for col in date_cols:
        if formatted_df[col].dtype == 'object':
            formatted_df[col] = formatted_df[col].apply(parse_date)
    
    # Add styling
    styled_df = formatted_df.style\
        .set_properties(**{
            'background-color': 'white',
            'color': 'black',
            'border-color': 'lightgrey',
            'border-style': 'solid',
            'border-width': '1px',
            'padding': '5px'
        })\
        .set_table_styles([
            {'selector': 'th',
             'props': [('background-color', '#f0f0f0'),
                      ('color', 'black'),
                      ('font-weight', 'bold'),
                      ('border-color', 'lightgrey'),
                      ('border-style', 'solid'),
                      ('border-width', '1px'),
                      ('padding', '5px')]},
            {'selector': 'tr:nth-of-type(odd)',
             'props': [('background-color', '#f9f9f9')]},
            {'selector': 'tr:hover',
             'props': [('background-color', '#f0f0f0')]}
        ])
    
    return styled_df

def create_viewable_dataframe(raw_data, array_columns):
    """Convert raw data to a viewable DataFrame format"""
    # Convert list of dictionaries to DataFrame
    df = pd.DataFrame(raw_data)
    
    # For each array column, replace with summary statistics
    for col in array_columns:
        if col in df.columns:
            df[col] = df[col].apply(
                lambda x: f"Array[{len(x)}] - Mean: {np.mean(x):.3e}, Std: {np.std(x):.3e}"
                if isinstance(x, np.ndarray) else x
            )
    
    return df

def main():
    # Get the current directory
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Define the folder locations and database path
    folder_locations = [
        os.path.join(current_dir, 'data', 'Sinton_FMT'),
        os.path.join(current_dir, 'data', 'EL_DSLR_CMOS')
    ]
    sqlite_file_path = os.path.join(os.path.dirname(current_dir), 'PVMCF_Database.db')

    # Create parser instance
    parser = InstrumentDataParser(folder_locations, sqlite_file_path)

    # Parse both datasets
    print("Parsing image metadata...")
    image_data, failed_image_files = parser.parse_image_metadata()
    
    print("\nParsing Sinton FMT data...")
    sinton_data, failed_sinton_files = parser.parse_sinton_fmt_metadata()
    
    if not image_data and not sinton_data:
        print("No data found. Please check the file paths and ensure data files exist.")
        return
    
    # Create viewable DataFrames
    if image_data:
        image_df = create_viewable_dataframe(image_data, [])
        formatted_image_df = format_dataframe(image_df)
        # Save image data
        image_output_file = 'el_image_data.csv'
        image_df.to_csv(image_output_file, index=False)
        print(f"\nImage data saved to {image_output_file}")
    else:
        image_df = pd.DataFrame()
        formatted_image_df = None
    
    if sinton_data:
        sinton_df = create_viewable_dataframe(sinton_data, parser.arrays)
        formatted_sinton_df = format_dataframe(sinton_df)
        # Save Sinton data
        sinton_output_file = 'sinton_data.csv'
        sinton_df.to_csv(sinton_output_file, index=False)
        print(f"Sinton data saved to {sinton_output_file}")
    else:
        sinton_df = pd.DataFrame()
        formatted_sinton_df = None
    
    # Return all DataFrames for IDE display
    return {
        'raw': {
            'image': image_df,
            'sinton': sinton_df
        },
        'formatted': {
            'image': formatted_image_df,
            'sinton': formatted_sinton_df
        }
    }

if __name__ == "__main__":
    dataframes = main()  