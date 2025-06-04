import os
from instrument_data_parser_oo import InstrumentDataParser

def main():
    # Get the current directory
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Define the database path (relative to the script location)
    db_path = os.path.join(os.path.dirname(current_dir), 'PVMCF_Database.db')
    
    # Define the folder locations where your data files are stored
    folder_locations = [
        os.path.join(current_dir, 'data', 'EL_DSLR_CMOS'),  # For EL images
        os.path.join(current_dir, 'data', 'Sinton_FMT')     # For IV curves
    ]
    
    # Create the parser instance
    parser = InstrumentDataParser(
        folder_locations=folder_locations,
        sqlite_file_path=db_path
    )
    
    # Test parsing image metadata
    print("Parsing image metadata...")
    image_metadata, failed_image_files = parser.parse_image_metadata()
    print(f"Successfully processed {len(image_metadata)} images")
    print(f"Failed to process {len(failed_image_files)} images")
    if failed_image_files:
        print("Failed files:", failed_image_files)
    
    # Test parsing Sinton FMT metadata
    print("\nParsing Sinton FMT metadata...")
    sinton_metadata, failed_sinton_files = parser.parse_sinton_fmt_metadata()
    print(f"Successfully processed {len(sinton_metadata)} IV curves")
    print(f"Failed to process {len(failed_sinton_files)} IV curves")
    if failed_sinton_files:
        print("Failed files:", failed_sinton_files)
    
    # Print some sample data
    if not image_metadata.empty:
        print("\nSample image metadata:")
        print(image_metadata.head())
    
    if not sinton_metadata.empty:
        print("\nSample Sinton metadata:")
        print(sinton_metadata.head())

if __name__ == "__main__":
    main() 