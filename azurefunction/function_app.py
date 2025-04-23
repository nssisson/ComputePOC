import azure.functions as func
import logging
import sys
import os
import json
import src.WriteAzureBlob as WriteAzureBlob
import src.QueryAzureBlobParquet as QueryAzureBlobParquet
import src.Extract_FRED_Data as extract_data
import src.Transform_Load_FREDBIGTABLE as transform_data

#function_dir = os.path.dirname(os.path.abspath(__file__))
#application_code_path = os.path.abspath(os.path.join(function_dir, '..', 'src'))
#if application_code_path not in sys.path:
#    sys.path.append(application_code_path)

#logging.info(sys.path)

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

function_map = {
    "extract_data": extract_data.main,
    "transform_data": transform_data.main
}

@app.route(route="computepoc_azurefunction")
def computepoc_azurefunction(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')


    funcname = req.params.get('funcname')
    if not funcname:
        try:
            req_body = req.get_json()
        except ValueError:
            pass
        else:
            funcname = req_body.get('funcname')
    
    if funcname:
        target_function = function_map.get(funcname)
        target_function()
        return func.HttpResponse(
        json.dumps({"status": "success", "result": "Funciton Execution Completed"}),
        mimetype="application/json",
        status_code=200
        )

    else:
        return func.HttpResponse(
             "This HTTP triggered function executed successfully. Pass a funcname in the query string or in the request body for a personalized response.",
             status_code=200
        )