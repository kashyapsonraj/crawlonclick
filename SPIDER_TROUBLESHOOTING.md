# Troubleshooting Spider Output Files

This document provides information on how to troubleshoot issues with spider output files not being generated correctly.

## Common Issues and Solutions

1. **Output Directory Doesn't Exist**: The application now automatically creates the output directory if it doesn't exist.

2. **MongoDB Connection Issues**: If MongoDB is not available or has connection issues, direct file output has been added as a fallback mechanism.

3. **Environment Variables**: Make sure the SCRAPY_JOB environment variable is being correctly set and accessed.

4. **File Path Confusion**: The application now checks multiple possible file paths and formats.

5. **Spider Errors**: Error handling has been improved to create output files even when errors occur.

## Testing Spider Execution

You can test spider execution directly using the `test_spider_run.py` script:

```
python scripts/test_spider_run.py TestSpider
```

This will run the TestSpider and verify that output files are being created correctly.

## Manual Testing of runspider API

The runspider API can be tested manually by:

1. Make sure you're logged in to the application
2. Navigate to a job with an attached spider
3. Try running the spider and check the logs for any errors
4. Examine the output directory to see if files are being created

## Spider Implementation Requirements

For a spider to work correctly with the system, it should:

1. Define a `name` attribute
2. Define a `client_identifier` attribute (for MongoDB collection name)
3. Implement a `parse` method that yields items
4. Optionally, implement a direct file output mechanism as a fallback

Example:

```python
class MySpider(scrapy.Spider):
    name = "MySpider"
    start_urls = ['https://example.com']
    client_identifier = 'my_collection'

    def parse(self, response):
        # Extract data
        yield {
            'title': 'Example Title',
            'content': 'Example Content'
        }
```

## Debugging Tips

- Check the logs for any errors during spider execution
- Verify the MongoDB connection is working
- Ensure the output directory exists and is writable
- Try running the spider directly using the scrapy command line tool
