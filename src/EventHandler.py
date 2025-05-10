import azure.storage.queue as queue
#import logging
from azure.identity import DefaultAzureCredential
import Extract_FRED_Data
import Transform_Load_FREDBIGTABLE
import Extract_FRED_Data_ALL
import Transform_Load_FREDBIGTABLE_ALL
import WriteAzureBlob
import json
import os

# Configure logging to display debug messages
#logging.basicConfig(level=logging.DEBUG)

# Initialize the QueueClient with DefaultAzureCredential
storage_account_name = os.environ.get('STORAGE_ACCOUNT_NAME')
if storage_account_name is None:
    storage_account_name = 'computepocstorage'
queueName = os.environ.get('QUEUE_NAME')
print(queueName)
if queueName is None:
    queueName = 'testqueue'
account_url = f"https://{storage_account_name}.queue.core.windows.net/"
queue_client = queue.QueueClient(
    account_url=account_url,
    queue_name=queueName,
    credential=DefaultAzureCredential()
    #,connection_verify=False #uncomment to run locally with certificate issue
)

function_map = {
    'Extract_FRED_Data': Extract_FRED_Data.main,
    'Transform_Load_FREDBIGTABLE': Transform_Load_FREDBIGTABLE.main,
    'Extract_FRED_Data_ALL': Extract_FRED_Data_ALL.main,
    'Transform_Load_FREDBIGTABLE_ALL': Transform_Load_FREDBIGTABLE_ALL.main
}

request = {}
response = {}
try:
    message = queue_client.receive_message(visibility_timeout = 5)
    queue_client.delete_message(message)
    request = json.loads(message.content)
    print(f"Processing message: {message.content}")
    task = function_map[request["Process"]]
    response = task()
    WriteAzureBlob.writeJsonToBlob("logging", f"{request['ExecutionId']}/{request['Process']}.json", response)
except Exception as e:
    response["status"] = 'fail'
    response["output"] = {}
    response["output"]["error"] = str(e)
    WriteAzureBlob.writeJsonToBlob("logging", f"{request['ExecutionId']}/{request['Process']}.json", response)
    print('There was a problem processing the message or task.')


