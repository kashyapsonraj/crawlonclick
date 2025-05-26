#!/usr/bin/env python
"""
Direct test script to verify file creation in the output directory
"""

import os
import json
import sys
from datetime import datetime

def test_file_creation():
    """
    Test creating files directly in the output directory
    """
    print("Testing direct file creation in output directory")
    
    # Get the current working directory
    cwd = os.getcwd()
    print(f"Current working directory: {cwd}")
    
    # Define paths to try
    paths_to_try = [
        os.path.join(cwd, "output"),
        os.path.join(cwd, "scrapy_framework", "output"),
        "output"
    ]
    
    for path in paths_to_try:
        print(f"\nTrying path: {path}")
        
        # Check if directory exists
        if not os.path.exists(path):
            try:
                os.makedirs(path)
                print(f"  Created directory: {path}")
            except Exception as e:
                print(f"  Error creating directory: {e}")
                continue
        else:
            print(f"  Directory exists: {path}")
        
        # Try to create test files
        test_file_base = f"test_file_{datetime.now().strftime('%H%M%S')}"
        
        try:
            # Create JSON file
            json_path = os.path.join(path, f"{test_file_base}.json")
            data = {
                "test": "Direct file creation test",
                "timestamp": datetime.now().isoformat(),
                "path": path
            }
            
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            
            print(f"  Created JSON file: {json_path}")
            
            # Create CSV file
            csv_path = os.path.join(path, f"{test_file_base}.csv")
            with open(csv_path, 'w', encoding='utf-8') as f:
                f.write("column1,column2,column3\n")
                f.write(f"test,{datetime.now().isoformat()},{path}\n")
            
            print(f"  Created CSV file: {csv_path}")
            
            # List files in the directory
            files = os.listdir(path)
            print(f"  Files in directory: {files}")
            
            return True
        except Exception as e:
            print(f"  Error creating files in {path}: {e}")
    
    return False

if __name__ == "__main__":
    success = test_file_creation()
    if success:
        print("\nSUCCESS: File creation test passed!")
        sys.exit(0)
    else:
        print("\nFAILED: Could not create files in any output directory")
        sys.exit(1)
