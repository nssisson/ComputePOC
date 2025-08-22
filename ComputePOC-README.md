# Compute POC
A proof of concept to demonstrate the capability of python for data engineering tasks when run in Azure Container App Jobs

## Requirements

Python 3.xx
Terraform v1.12.2 +
Reference ./requirements.txt for python libraries

## Terraform

The Infrastructure for the Azure Container App is defined in terraform. To deploy the terraform, the deploying user (or service principal) will need owner permissions over the target subscription. 

Note that for the first deployment, we expect a two step deployment. The terraform deployment succeding depends on the docker container being deployed to the Azure Container Registry to complete successfully (referenced in the container apps). Because the Azure Container Registry is deployed in the same codebase, we have to deploy, wait for the deploy to fail on the Container Apps step, push the docker container to the newly created Azure Container Registry, then deploy again. This is only a one time caveat when first deploying the solution. The alternative would be to deploy the Container to the registry within the terraform deployment, but this is very hack and not the best practice. We will be deploying the containers using Azure Devops Pipelines, not using terraform.

## Samples

Jobs are started by pushing messages to the created Azure Storage Queues. For the pupose of this poc, the following would do:

### Extract:
{
"ExecutionId":"1",
"Process":"Extract_FRED_Data"
}

### Transform:
{
"ExecutionId":"2",
"Process":"Transform_Load_FREDBIGTABLE"
}

##IMA Environment workarounds

When running the POC you will need to remove the commented out lines of code that says "connection_verify=False " in the files EventHandler.py, QueryAzureBlobParquet.py and WriteAzureBlob.py

When logging into the Azure Container Registry you will receive an SSL certificate issue. The only way I have found to workaround this issue is to update the environemnt variable AZURE_CLI_DISABLE_CONNECTION_VERIFICATION = 1