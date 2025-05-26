#!/usr/bin/env python
"""
Simple test script to run a spider directly and create output files
"""

import os
import sys
import subprocess
import json
import uuid
from datetime import datetime

def run_test_spider():
    # Generate a unique job ID
    job_id = str(uuid.uuid4()).replace('-', '')[:16]
    print(f"Testing spider with job ID: {job_id}")
    
    # Make sure output directory exists
    output_dir = os.path.join(os.getcwd(), "output")
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"Created output directory: {output_dir}")
    
    # Set environment variables
    env = os.environ.copy()
    env['SCRAPY_JOB'] = job_id
    
    # Run the spider directly
    cmd = 'scrapy crawl TestSpider'
    print(f"Running command: {cmd}")
    
    try:
        result = subprocess.run(
            cmd,
            env=env,
            shell=True,
            capture_output=True,
            text=True,
            timeout=120
        )
        
        print(f"Command returned with code: {result.returncode}")
        
        if result.stdout:
            print("STDOUT:")
            print(result.stdout[:500])  # Print first 500 chars
            
        if result.stderr:
            print("STDERR:")
            print(result.stderr[:500])  # Print first 500 chars
        
        # Check if output files were created
        print("\nChecking output files:")
        
        if os.path.exists(output_dir):
            files = os.listdir(output_dir)
            print(f"Files in output directory: {files}")
            
            # Look for job ID files
            job_files = [f for f in files if job_id in f]
            if job_files:
                print(f"Found files with job ID: {job_files}")
            else:
                print(f"No files found with job ID: {job_id}")
            
            # Look for TestSpider files
            spider_files = [f for f in files if "TestSpider" in f]
            if spider_files:
                print(f"Found files with spider name: {spider_files}")
            else:
                print(f"No files found with spider name: TestSpider")
        else:
            print(f"Output directory {output_dir} does not exist!")
        
        # If no files were found, create a manual output file
        if not (job_files or spider_files):
            # Create fallback data
            backup_file = os.path.join(output_dir, f"TestSpider_manual_{job_id}.json")
            print(f"Creating manual backup file: {backup_file}")
            
            data = [
                {
                    "Title": "Manual Test Data",
                    "Text": "Generated because no spider output was found",
                    "Image": "https://example.com/image.jpg",
                    "JobID": job_id,
                    "Timestamp": datetime.now().isoformat()
                }
            ]
            
            with open(backup_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            
            print(f"Manual backup file created: {backup_file}")
        
    except subprocess.TimeoutExpired:
        print("Command timed out after 120 seconds")
    except Exception as e:
        print(f"Error running command: {e}")

if __name__ == "__main__":
    run_test_spider()
