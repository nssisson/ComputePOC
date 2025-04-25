import azure.storage.queue as queue
#import logging
from azure.identity import DefaultAzureCredential
import Extract_FRED_Data
import Transform_Load_FREDBIGTABLE
import WriteAzureBlob
import json

# Configure logging to display debug messages
#logging.basicConfig(level=logging.DEBUG)

# Initialize the QueueClient with DefaultAzureCredential
queue_client = queue.QueueClient(
    account_url="https://computepocstorage.queue.core.windows.net/",
    queue_name="computepocqueue",
    #queue_name="testqueue",
    credential = DefaultAzureCredential()
    #,connection_verify=False #uncomment to run locally with certificate issue
)

function_map = {
    'Extract_FRED_Data': Extract_FRED_Data.main,
    'Transform_Load_FREDBIGTABLE': Transform_Load_FREDBIGTABLE.main
}

message = queue_client.receive_message(visibility_timeout = 5)
request = {}
response = {}
if message is not None:
    try:
        queue_client.delete_message(message)
        print("Message Dequeued") 
        request = json.loads(message.content)
        print(f"Processing message: {message.content}")
        if function_map[request["Process"]]:
            task = function_map[request["Process"]]
            output = task()
            WriteAzureBlob.writeJsonToBlob("logging", f"{request['ExecutionId']}/{request['Process']}.json", output)
        else:
            print('Not a valid function')
    except:
        print('There was a problem processing the message or task.')
else:
    print('Nothing Queued')

