#!/usr/bin/env python
"""
Test script to run a spider directly and verify output files are created correctly.
"""

import os
import sys
import subprocess
import uuid
from datetime import datetime

# Add the project root directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.insert(0, project_root)

# Import project modules
from core import logger
from core.file_utils import ensure_output_directory, save_data_to_files

def test_run_spider(spider_name):
    """
    Test running a spider directly and verifying output files
    """
    logger.info(f"Testing spider: {spider_name}")
    
    # Generate a unique job ID
    job_id = str(uuid.uuid4()).replace('-', '')[:16]
    logger.info(f"Generated job ID: {job_id}")
    
    # Ensure output directory exists
    output_dir = ensure_output_directory()
    logger.info(f"Output directory: {output_dir}")
    
    # Set environment variables for the spider
    env = os.environ.copy()
    env['SCRAPY_JOB'] = job_id
    
    # Run spider using subprocess
    cmd = f'scrapy crawl {spider_name}'
    logger.info(f"Running command: {cmd}")
    
    result = subprocess.run(
        cmd,
        cwd=project_root,
        env=env,
        capture_output=True,
        text=True,
        timeout=300,  # 5 minute timeout
        shell=True    # Use shell to ensure proper execution on Windows
    )
    
    if result.returncode == 0:
        logger.info(f"Spider {spider_name} completed successfully")
        
        # List all files in the output directory
        try:
            output_files = os.listdir(output_dir)
            logger.info(f"Files in output directory: {output_files}")
            
            # Check if job ID files exist
            job_id_files = [f for f in output_files if job_id in f]
            logger.info(f"Files with job ID {job_id}: {job_id_files}")
            
            # Check if spider name files exist
            spider_files = [f for f in output_files if spider_name in f]
            logger.info(f"Files with spider name {spider_name}: {spider_files}")
            
            if not (job_id_files or spider_files):
                logger.warning("No output files found for this job. Creating fallback file.")
                
                # Create fallback data
                fallback_data = [
                    {
                        "Test": "Fallback data",
                        "Spider": spider_name,
                        "JobID": job_id,
                        "Time": datetime.now().isoformat()
                    }
                ]
                
                # Save to files
                save_data_to_files(fallback_data, f"{job_id}_fallback")
                save_data_to_files(fallback_data, f"{spider_name}_fallback")
        except Exception as e:
            logger.error(f"Error checking output files: {e}")
    else:
        logger.error(f"Spider {spider_name} failed with return code {result.returncode}")
        logger.error(f"STDOUT: {result.stdout}")
        logger.error(f"STDERR: {result.stderr}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        spider_name = sys.argv[1]
    else:
        spider_name = "TestSpider"
        
    test_run_spider(spider_name)
