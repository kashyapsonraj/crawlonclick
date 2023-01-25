# Define your item pipelines here #
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
import os

import pandas as pd
import os
from itemadapter import ItemAdapter
from core import logger, config
from core.db_util import MongoDBUtil
from datetime import datetime
import uuid

class MongoDBPipeline:

    def open_mongodb_conn(self, spider):
        connection = MongoDBUtil.get_conn()
        db = connection[config.MONGO_DB_NAME]
        self.collection = db[spider.client_identifier]

    def open_spider(self, spider):
        print("Open Spider", spider.name)
        self.open_mongodb_conn(spider)
        self.unique_id = str(uuid.uuid1())
        self.today_date = datetime.now()

    def insert_mongo_item(self,item):
        item = dict(item)
        item.update({"uuid": self.unique_id})
        self.collection.insert_one(item)

    def process_item(self, item, spider):
        print("process item", spider)
        logger.info("Process Item: " + str(spider))
        self.insert_mongo_item(item)

    def csv_mongo_data_export(self, spider):
        find_results = self.collection.find({"uuid": self.unique_id})
        df = pd.DataFrame(list(find_results))
        if not df.empty:
            df = df.drop(['_id', 'uuid'], axis=1)
            file_name = "./output/" + os.environ["SCRAPY_JOB"]
            df.to_csv(file_name, index=False)
            df.to_excel(file_name, index=False)
        else:
            logger.info("NO DATA TO EXPORT.")

    def close_spider(self, spider):
        print("close spider", spider)
        self.csv_mongo_data_export(spider)
