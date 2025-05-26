"""
Utility functions for handling file output operations
"""
import os
import csv
import json
import pandas as pd
from core import logger

def ensure_output_directory(base_dir=None):
    """
    Ensure the output directory exists
    """
    if base_dir is None:
        base_dir = os.getcwd()
        
    output_dir = os.path.join(base_dir, "output")
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        logger.info(f"Created missing output directory: {output_dir}")
    
    return output_dir

def save_data_to_files(data, file_basename, base_dir=None):
    """
    Save data to CSV, Excel, and JSON files
    
    Args:
        data: List of dictionaries containing data
        file_basename: Base filename (without extension)
        base_dir: Base directory (defaults to current working directory)
        
    Returns:
        dict: Paths to created files
    """
    try:
        # Get output directory
        output_dir = ensure_output_directory(base_dir)
        
        file_paths = {}
        
        # Save as CSV
        csv_path = os.path.join(output_dir, f"{file_basename}.csv")
        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            if data and len(data) > 0:
                writer = csv.DictWriter(f, fieldnames=data[0].keys())
                writer.writeheader()
                writer.writerows(data)
            else:
                # Create empty file with header
                f.write("No data found\n")
        file_paths['csv'] = csv_path
        
        # Save as Excel if data exists
        if data and len(data) > 0:
            excel_path = os.path.join(output_dir, f"{file_basename}.xlsx")
            df = pd.DataFrame(data)
            df.to_excel(excel_path, index=False)
            file_paths['excel'] = excel_path
        
        # Save as JSON
        json_path = os.path.join(output_dir, f"{file_basename}.json")
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        file_paths['json'] = json_path
        
        logger.info(f"Files created: {', '.join(file_paths.values())}")
        return file_paths
    
    except Exception as e:
        logger.error(f"Error saving data to files: {str(e)}")
        return {}
