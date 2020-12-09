# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter


class InternalLinkingPipeline:
    def process_item(self, item, spider):
        if item['Text']:
            result = ""
            for element in item['Text']:
                result += f"{element} "
            item['Text'] = result[:-1]
        return item
