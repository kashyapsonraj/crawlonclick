# Define your item pipelines here #
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
import os
import pandas as pd
import json
import csv
from itemadapter import ItemAdapter
from core import logger, config
from core.db_util import MongoDBUtil
from datetime import datetime
import uuid
import traceback

class MongoDBPipeline:

    def __init__(self):
        self.mongo_available = False
        self.items = []  # Store items locally if MongoDB fails
        self.unique_id = str(uuid.uuid1())
        self.today_date = datetime.now()
        self.collection = None

    def open_mongodb_conn(self, spider):
        try:
            connection = MongoDBUtil.get_conn()
            db = connection[config.MONGO_DB_NAME]
            self.collection = db[spider.client_identifier]
            self.mongo_available = True
            logger.info("MongoDB connection established successfully")
        except Exception as e:
            self.mongo_available = False
            logger.error(f"MongoDB connection failed: {str(e)}")
            logger.error(traceback.format_exc())
            # Create output directory for direct file writing fallback
            self.ensure_output_dir()

    def ensure_output_dir(self):
        """Ensure output directory exists for direct file writing"""
        output_dirs = [
            os.path.join(os.getcwd(), "output"),
            os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "output"))
        ]
        
        for output_dir in output_dirs:
            try:
                if not os.path.exists(output_dir):
                    os.makedirs(output_dir)
                    logger.info(f"Created output directory: {output_dir}")
                return output_dir
            except Exception as e:
                logger.error(f"Failed to create output directory {output_dir}: {e}")
        
        return os.path.join(os.getcwd(), "output")  # Default fallback

    def open_spider(self, spider):
        logger.info(f"Opening spider: {spider.name}")
        print("Open Spider", spider.name)
        try:
            self.open_mongodb_conn(spider)
        except Exception as e:
            logger.error(f"Error in open_spider: {e}")
            self.mongo_available = False
        
        # Set job ID from environment or generate a new one
        self.job_id = os.environ.get("SCRAPY_JOB", self.unique_id)
        logger.info(f"Using job ID: {self.job_id}")

    def insert_mongo_item(self, item):
        if not self.mongo_available:
            # Store item locally if MongoDB is not available
            self.items.append(dict(item))
            return
            
        try:
            item_dict = dict(item)
            item_dict.update({"uuid": self.unique_id})
            self.collection.insert_one(item_dict)
        except Exception as e:
            logger.error(f"Failed to insert item to MongoDB: {e}")
            # Store item locally as fallback
            self.items.append(dict(item))

    def process_item(self, item, spider):
        logger.info(f"Processing item for spider {spider.name}")
        print("process item", spider)
        
        # Always store a local copy
        self.items.append(dict(item))
        
        # Try to insert to MongoDB if available
        if self.mongo_available:
            try:
                self.insert_mongo_item(item)
            except Exception as e:
                logger.error(f"Error in process_item: {e}")
        
        return item
        
    def export_to_files(self, items, spider):
        """Export items directly to files"""
        if not items:
            logger.warning("No items to export")
            return
            
        try:
            # Ensure output directory exists
            output_dir = self.ensure_output_dir()
            
            # Get job ID
            job_id = self.job_id
            spider_name = spider.name
            
            # Create DataFrame
            df = pd.DataFrame(items)
            
            # Save CSV files
            job_csv = os.path.join(output_dir, f"{job_id}.csv")
            spider_csv = os.path.join(output_dir, f"{spider_name}.csv")
            
            df.to_csv(job_csv, index=False)
            df.to_csv(spider_csv, index=False)
            logger.info(f"Saved CSV files: {job_csv}, {spider_csv}")
            
            # Save Excel files
            job_excel = os.path.join(output_dir, f"{job_id}.xlsx")
            spider_excel = os.path.join(output_dir, f"{spider_name}.xlsx")
            
            df.to_excel(job_excel, index=False)
            df.to_excel(spider_excel, index=False)
            logger.info(f"Saved Excel files: {job_excel}, {spider_excel}")
            
            # Save JSON files for good measure
            job_json = os.path.join(output_dir, f"{job_id}.json")
            spider_json = os.path.join(output_dir, f"{spider_name}.json")
            
            with open(job_json, 'w', encoding='utf-8') as f:
                json.dump(items, f, indent=2)
                
            with open(spider_json, 'w', encoding='utf-8') as f:
                json.dump(items, f, indent=2)
                
            logger.info(f"Saved JSON files: {job_json}, {spider_json}")
            
            # List files in directory
            try:
                dir_contents = os.listdir(output_dir)
                logger.info(f"Files in output directory: {dir_contents}")
            except Exception as e:
                logger.error(f"Error listing output directory: {e}")
                
            return True
        except Exception as e:
            logger.error(f"Error exporting files: {e}")
            logger.error(traceback.format_exc())
            return False
        
    def csv_mongo_data_export(self, spider):
        """Export data from MongoDB to files"""
        try:
            if not self.mongo_available or not self.collection:
                logger.warning("MongoDB not available, using local items for export")
                return self.export_to_files(self.items, spider)
                
            # Try to get data from MongoDB
            find_results = self.collection.find({"uuid": self.unique_id})
            items_from_db = list(find_results)
            
            if items_from_db:
                # Clean up MongoDB items
                for item in items_from_db:
                    if '_id' in item:
                        del item['_id']
                    if 'uuid' in item:
                        del item['uuid']
                        
                logger.info(f"Found {len(items_from_db)} items in MongoDB")
                return self.export_to_files(items_from_db, spider)
            else:
                logger.warning("No items found in MongoDB, using local items")
                return self.export_to_files(self.items, spider)
        except Exception as e:
            logger.error(f"Error in csv_mongo_data_export: {e}")
            logger.error(traceback.format_exc())
            # Fallback to local items
            return self.export_to_files(self.items, spider)

    def close_spider(self, spider):
        print("close spider", spider)
        logger.info(f"Closing spider {spider.name}, exporting data")
        
        try:
            success = self.csv_mongo_data_export(spider)
            if not success and self.items:
                # One last attempt with direct file writing
                self.direct_file_export(spider)
        except Exception as e:
            logger.error(f"Error in close_spider: {e}")
            logger.error(traceback.format_exc())
            # One last attempt with direct file writing
            self.direct_file_export(spider)
    
    def direct_file_export(self, spider):
        """Last resort direct file export"""
        try:
            if not self.items:
                logger.warning("No items to export in direct_file_export")
                return
                
            # Ensure output directory exists
            output_dir = os.path.join(os.getcwd(), "output")
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
                
            # Write directly to files
            job_csv = os.path.join(output_dir, f"{self.job_id}_direct.csv")
            spider_csv = os.path.join(output_dir, f"{spider.name}_direct.csv")
            
            # Use CSV writer directly
            fieldnames = self.items[0].keys()
            
            with open(job_csv, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(self.items)
                
            with open(spider_csv, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(self.items)
                
            logger.info(f"Direct file export complete: {job_csv}, {spider_csv}")
        except Exception as e:
            logger.error(f"Error in direct_file_export: {e}")
            logger.error(traceback.format_exc())

    def close_spider(self, spider):
        print("close spider", spider)
        self.csv_mongo_data_export(spider)
