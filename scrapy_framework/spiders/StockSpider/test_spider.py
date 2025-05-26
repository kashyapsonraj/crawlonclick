import scrapy
import os
import sys
from datetime import datetime
import json
import csv
import pandas as pd
from scrapy.exceptions import DropItem

class TestSpider(scrapy.Spider):
    name = "TestSpider"
    start_urls = ['https://webscraper.io/test-sites']
    client_identifier = 'test'

    def __init__(self, *args, **kwargs):
        super(TestSpider, self).__init__(*args, **kwargs)
        # Try to get the job ID from environment
        self.job_id = os.environ.get('SCRAPY_JOB', 'default_job_id')
        self.logger.info(f"Spider initialized with job ID: {self.job_id}")
        
        # Track all items for direct output
        self.all_items = []

    def parse(self, response):
        self.logger.info(f"Parsing response from {response.url}")
        try:
            # Log that we're generating items
            self.logger.info("Generating test data items")
            
            # Generate some test data
            items = [
                {
                    'Title': "Sample Product 1",
                    'Text': "This is a sample product description",
                    'Image': "https://example.com/image1.jpg",
                    'Price': "$10.99"
                },
                {
                    'Title': "Sample Product 2",
                    'Text': "Another sample product with details",
                    'Image': "https://example.com/image2.jpg",
                    'Price': "$24.99"
                },
                {
                    'Title': "Sample Product 3",
                    'Text': "Third sample product information",
                    'Image': "https://example.com/image3.jpg",
                    'Price': "$15.50"
                }
            ]
            
            # Store all items for direct output at the end
            self.all_items.extend(items)
            
            # Create direct output files immediately
            self.create_direct_output(items)
            
            # Yield items for the pipeline
            for item in items:
                self.logger.info(f"Yielding item: {item['Title']}")
                yield item
                
        except Exception as e:
            self.logger.error(f"Error in parse: {str(e)}")
            # Yield at least one item so pipeline runs
            error_item = {
                'Title': "Error occurred",
                'Text': f"Error: {str(e)}",
                'Image': "N/A",
                'Price': "N/A"
            }
            self.all_items.append(error_item)
            yield error_item
    
    def create_direct_output(self, items):
        """Create output files directly as a backup mechanism"""
        try:
            # Try different output directories
            output_dirs = [
                os.path.join(os.getcwd(), "output"),
                os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "output")),
                os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "output"))
            ]
            
            for output_dir in output_dirs:
                self.logger.info(f"Trying output directory: {output_dir}")
                
                try:
                    # Ensure output directory exists
                    if not os.path.exists(output_dir):
                        os.makedirs(output_dir)
                        self.logger.info(f"Created directory: {output_dir}")
                    
                    # Generate CSV with spider name
                    spider_csv = os.path.join(output_dir, f"{self.name}.csv")
                    with open(spider_csv, 'w', newline='', encoding='utf-8') as f:
                        writer = csv.DictWriter(f, fieldnames=items[0].keys())
                        writer.writeheader()
                        writer.writerows(items)
                    self.logger.info(f"Created spider CSV: {spider_csv}")
                    
                    # Generate CSV with job ID
                    job_csv = os.path.join(output_dir, f"{self.job_id}.csv")
                    with open(job_csv, 'w', newline='', encoding='utf-8') as f:
                        writer = csv.DictWriter(f, fieldnames=items[0].keys())
                        writer.writeheader()
                        writer.writerows(items)
                    self.logger.info(f"Created job ID CSV: {job_csv}")
                    
                    # Generate Excel with spider name
                    df = pd.DataFrame(items)
                    spider_excel = os.path.join(output_dir, f"{self.name}.xlsx")
                    df.to_excel(spider_excel, index=False)
                    self.logger.info(f"Created spider Excel: {spider_excel}")
                    
                    # Generate Excel with job ID
                    job_excel = os.path.join(output_dir, f"{self.job_id}.xlsx")
                    df.to_excel(job_excel, index=False)
                    self.logger.info(f"Created job ID Excel: {job_excel}")
                    
                    # Print directory contents for debugging
                    dir_contents = os.listdir(output_dir)
                    self.logger.info(f"Output directory contents: {dir_contents}")
                    
                    # Successfully created files, so return
                    return
                except Exception as e:
                    self.logger.error(f"Error creating files in {output_dir}: {str(e)}")
            
            # If we get here, couldn't create files in any directory
            self.logger.error("Could not create output files in any directory")
            
        except Exception as e:
            self.logger.error(f"Error in create_direct_output: {str(e)}")
            
    def closed(self, reason):
        """Called when spider is closed"""
        self.logger.info(f"Spider closed with reason: {reason}")
        
        # Try to write all collected items again to ensure output files exist
        if self.all_items:
            self.logger.info(f"Writing {len(self.all_items)} items to files at close")
            self.create_direct_output(self.all_items)
        else:
            self.logger.warning("No items collected during spider run")
        # Uncomment for local testing:
# from scrapy.cmdline import execute
# execute('scrapy crawl TestSpider'.split())