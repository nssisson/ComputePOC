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
    queue_name="computepocqueue",
    credential = DefaultAzureCredential()
    #,connection_verify=False #uncomment to run locally with certificate issue
)

function_map = {
    'Extract_FRED_Data': Extract_FRED_Data.main,
    'Transform_Load_FREDBIGTABLE': Transform_Load_FREDBIGTABLE.main
}

message = queue_client.receive_message(visibility_timeout = 5)

if message is not None:
    try:
        queue_client.delete_message(message)
        print("Message Deleted") 
        print(f"Processing message: {message.content}")
        task = function_map.get(message.content)
        output = task()
    except:
        print('There was a problem processing the message or task.')
else:
    print('Nothing Queued')

