import azure.storage.queue as queue
#import logging
from azure.identity import DefaultAzureCredential
import Extract_FRED_Data
import Transform_Load_FREDBIGTABLE

# Configure logging to display debug messages
#logging.basicConfig(level=logging.DEBUG)

# Initialize the QueueClient with DefaultAzureCredential
queue_client = queue.QueueClient(
    account_url="https://computepocstorage.queue.core.windows.net/",
    queue_name="testqueue",
    credential = DefaultAzureCredential(),
    connection_verify=False
)

function_map = {
    'Extract_FRED_Data': Extract_FRED_Data.main,
    'Transform_Load_FREDBIGTABLE': Transform_Load_FREDBIGTABLE.main
}
message = queue_client.receive_message(visibility_timeout=3500)
if message is not None:
    try: 
        print(f"Processing message: {message.content}")
        task = function_map.get(message.content)
        task()
    except:
        print('There was a problem processing the error.')
    finally:
        queue_client.delete_message(message)
else:
    print('Nothing Queued')

