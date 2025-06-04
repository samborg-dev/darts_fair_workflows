"""
@author: Sam Borges

Instrument Data Parser: Software for processing and parsing instrument data.

This script processes data from the following instruments:
    - Electroluminescence (EL) Images from DSLR/CMOS cameras
    - Sinton FMT (Flash Module Tester) measurements
    - IV (Current-Voltage) curve data
    - Module metadata and test conditions

The parser extracts and processes:
    - Image metadata (EXIF data, timestamps, camera settings)
    - Electrical measurements (IV curves, power measurements)
    - Test conditions (cycles, pressure, temperature)
    - Module identification and serial numbers

Events and Errors are tracked and logged in the console output.
"""

import os
import pandas as pd
import exifread
from PIL import Image
from PIL.TiffTags import TAGS
import file_management as fm
import SintonFMT_LIB

class InstrumentDataParser:
    def __init__(self, folder_locations, sqlite_file_path):
        self.folder_locations = folder_locations
        self.sqlite_file_path = sqlite_file_path
        self.failed_files = {}
        self.arrays = [
            'isc_array_raw', 'isc_array_interp', 'intensity_array', 
            'voc_array_raw', 'voc_array_interp', 'vload_array', 'vload_array_interp'
            ]

    def extract_image_metadata(self, image_file):
        if image_file.endswith(".jpg"):
            with open(image_file, 'rb') as f:
                exif_data = exifread.process_file(f, details=False)
            # Convert bytes to string if necessary
            return {tag: str(value) if isinstance(value, bytes) else value.printable for tag, value in exif_data.items()}
        elif image_file.endswith(".tif"):
            with Image.open(image_file) as img:
                tiff_dict = {TAGS[key]: str(img.tag[key]) for key in img.tag.iterkeys()}
            return tiff_dict

    def get_files_from_folders(self, folder_list=None, filetype='txt', filename_only=True):
        if folder_list is None:
            folder_list = self.folder_locations
        filetype_folder = []
        for folder in folder_list:
            for dirpath, dirnames, filenames in os.walk(folder):
                for filename in filenames:
                    if filename.endswith(f".{filetype}"):
                        if filename_only:
                            filetype_folder.append(filename.split('.')[0])
                        else:
                            file = os.path.join(dirpath, filename)
                            filetype_folder.append(file)
        return filetype_folder

    def parse_image_metadata(self):
        failed_files = []
        el_filepaths = self.get_files_from_folders(filetype='jpg', filename_only=False)
        print(f'{len(el_filepaths)} new files found for EL')
        frames = None
        for index, file in enumerate(el_filepaths):
            try:
                metadata_dict = fm.get_filename_metadata(file, 'el')
                exif_data = self.extract_image_metadata(file)
                exif_data.update(metadata_dict)
                exif_data['filename'] = file.split('\\')[-1]
                frame = pd.DataFrame.from_dict(exif_data, orient='index').T
                if index == 0:
                    frames = frame
                else:
                    frames = pd.concat([frames, frame], ignore_index=True)
            except Exception as e:
                print(f'{file} failed to be processed, please review. {e}')
                failed_files.append(file)
                continue
            if (index % 10 == 0):
                print(f'{index} EL Images processed so far...')
        
        if frames is not None:
            frames = frames.dropna(axis=1, how='all')
            frames = frames.loc[:, frames.notna().all(axis=0)]
            frames['camera'] = 'EL_CCD'
            Image_Metadata = frames.reset_index()
            return Image_Metadata, failed_files
        else:
            return pd.DataFrame(), failed_files

    def parse_sinton_fmt_metadata(self):
        failed_files = []
        mfr_filepaths = self.get_files_from_folders(filetype='mfr', filename_only=False)
        txt_filenames = self.get_files_from_folders(filetype='txt', filename_only=True)
        print(f'{len(mfr_filepaths)} new files found ending in .MFR')
        print(f'{len(txt_filenames)} new files found ending in .TXT')
        pd.set_option('display.max_colwidth', None)
        frames = None
        for index, file in enumerate(mfr_filepaths):
            try:
                data, content = SintonFMT_LIB.import_raw_data_from_file(file)
                metadata_dict = fm.get_filename_metadata(file, datatype='iv')
                corrected_data = SintonFMT_LIB.correct_raw_data(data)
                interpol_data = SintonFMT_LIB.interpolate_load_data(corrected_data)
                for array in self.arrays:
                    interpol_data[array] = interpol_data[array].tobytes()
                content = {item.split('=')[0]: item.split('=')[1].replace('"', '').strip() for item in content if '=' in item}
                content.update(metadata_dict)
                content.update(interpol_data)
                content['filepath'] = file
                content['filename'] = file.split('\\')[-1]
                if content['filename'].replace('IVT', '').strip('.mfr') in txt_filenames:
                    content['txt_file'] = content['filename'].replace('mfr', 'txt')
                else:
                    content['txt_file'] = 'N/A'
                if index == 0:
                    frames = pd.DataFrame.from_dict(content, orient='index').T
                else:
                    frames = pd.concat([frames, pd.DataFrame([content])], ignore_index=True)
            except Exception as e:
                print(f'{file} failed to be processed, please review. {e}')
                failed_files.append(file)
                continue
            if (index % 10 == 0):
                print(f'{index} IV curves processed so far...')
        if frames is not None:
            # Handle empty strings only in non-array columns
            non_array_cols = [col for col in frames.columns if col not in self.arrays]
            for col in non_array_cols:
                # First convert any non-string values to strings
                frames[col] = frames[col].astype(str)
                # Then convert empty strings to NaN
                frames[col] = frames[col].apply(lambda x: float('NaN') if x.strip() == "" else x)
            frames = frames.loc[:, frames.notna().all(axis=0)]
            Sinton_IV_Metadata = frames.reset_index()
            return Sinton_IV_Metadata, failed_files
        else:
            return pd.DataFrame(), failed_files

# Example usage:
# parser = InstrumentDataParser(folder_locations=['path/to/folders'], sqlite_file_path='path/to/sqlite.db')
# image_metadata, failed_image_files = parser.parse_image_metadata()
# sinton_metadata, failed_sinton_files = parser.parse_sinton_fmt_metadata() 