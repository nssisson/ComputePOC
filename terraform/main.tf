locals {
  base_name = "ima-aca-sbx-01"
  tags = {
    Owner       = "BI"
    Workload    = "ACA"
    Environment = "sbx"
    ManagedBy   = "Terraform"
  }

  registry   = "acrimaacasbx01.azurecr.io"
  image_name = "computepoc/computepoc"
  image_tag  = "latest"

  storage_containers = {
    "logging" = {
      role_assignments = {
        "ca_id-BlobContributor" = {
          role_definition_id_or_name = "Storage Blob Data Contributor"
          principal_id               = module.id.principal_id
        }
      }
    }
    "raw" = {
      role_assignments = {
        "ca_id-BlobContributor" = {
          role_definition_id_or_name = "Storage Blob Data Contributor"
          principal_id               = module.id.principal_id
        }
      }
    }
    "staging" = {
      role_assignments = {
        "ca_id-BlobContributor" = {
          role_definition_id_or_name = "Storage Blob Data Contributor"
          principal_id               = module.id.principal_id
        }
      }
    }
  }
  storage_filesystems = {
    # "raw"  = {}
  }
  storage_queues = {
    "queue0" = {
      role_assignments = {
        "ca_id-QueueContributor" = {
          role_definition_id_or_name = "Storage Queue Data Contributor"
          principal_id               = module.id.principal_id
        }
      }
    },
    "queue1" = {
      role_assignments = {
        "ca_id-QueueContributor" = {
          role_definition_id_or_name = "Storage Queue Data Contributor"
          principal_id               = module.id.principal_id
        }
      }
    }
  }
  private_endpoints_enabled = [
    "blob",
    "dfs",
    # "file",
    "queue",
    # "table",
    # "vault"
  ]
}

resource "azurerm_resource_group" "this" {
  name     = "rg-${local.base_name}"
  location = "Central US"
}

module "dls" {
  source           = "Azure/avm-res-storage-storageaccount/azurerm"
  version          = "0.6.1"
  enable_telemetry = false

  name                = replace("st-${local.base_name}", "-", "")
  resource_group_name = azurerm_resource_group.this.name
  location            = azurerm_resource_group.this.location
  tags                = local.tags

  account_replication_type = "LRS"
  account_kind             = "StorageV2"
  is_hns_enabled           = true

  containers = {
    for container_key, container in local.storage_containers :
    container_key => {
      name             = lookup(container, "name", container_key)
      role_assignments = lookup(container, "role_assignments", {})
      # future options
    }
  }
  queues = {
    for queue_key, queue in local.storage_queues :
    queue_key => {
      name             = lookup(queue, "name", queue_key)
      role_assignments = lookup(queue, "role_assignments", {})
      # future options
    }
  }
  storage_data_lake_gen2_filesystems = {
    for fs_key, fs in local.storage_filesystems :
    fs_key => {
      name = lookup(fs, "name", fs_key)
      # future options
    }
  }

  private_endpoints = { 
    for endpoint in toset(local.private_endpoints_enabled) :
    endpoint => {
      name                          = "pep-${endpoint}-${local.base_name}"
      network_interface_name        = "nic-pep-${endpoint}-${local.base_name}"
      subnet_resource_id            = module.vnet.subnets["pep"].resource_id
      subresource_name              = endpoint
      private_dns_zone_resource_ids = [module.privatelink.private_dns_zone_resource_ids[endpoint]]
    } if contains(["blob", "dfs", "file", "queue", "table", "web"], endpoint)
  }

  role_assignments = {
    "tf-BlobOwner" = {
      role_definition_id_or_name = "Storage Blob Data Owner"
      principal_id               = data.azurerm_client_config.current.object_id
    }
    "tf-QueueContributor" = {
      role_definition_id_or_name = "Storage Queue Data Contributor"
      principal_id               = data.azurerm_client_config.current.object_id
    }
  }

  public_network_access_enabled = true # Temporary
  network_rules = {
    ip_rules = [data.http.current_ip.response_body]
  }
}

#module "kv" {
#  source           = "Azure/avm-res-keyvault-vault/azurerm"
#  version          = "0.10.0"
#  enable_telemetry = false
#
#  name                = "kv-${local.base_name}"
#  resource_group_name = azurerm_resource_group.this.name
#  location            = azurerm_resource_group.this.location
#  tags                = local.tags
#  tenant_id           = data.azurerm_client_config.current.tenant_id
#
#  public_network_access_enabled = true  # Temporary
#  purge_protection_enabled      = false # Temporary
#
#  private_endpoints = contains(local.private_endpoints_enabled, "vault") ? {
#    "vault" = {
#      "name"                          = "pep-kv-${local.base_name}"
#      "network_interface_name"        = "nic-pep-kv-${local.base_name}"
#      "subnet_resource_id"            = module.vnet.subnets.pep.resource_id
#      "subresource_name"              = "vault"
#      "private_dns_zone_resource_ids" = [module.privatelink.private_dns_zone_resource_ids["vault"]]
#    }
#  } = {}
#
#  role_assignments = {
#    "tf-Administrator" = {
#      role_definition_id_or_name = "Key Vault Administrator"
#      principal_id               = data.azurerm_client_config.current.object_id
#    }
#  }
#}

module "log_analytics" {
  source           = "Azure/avm-res-operationalinsights-workspace/azurerm"
  version          = "0.4.2"
  enable_telemetry = false

  name                = "log-${local.base_name}"
  resource_group_name = azurerm_resource_group.this.name
  location            = azurerm_resource_group.this.location
  tags                = local.tags

  log_analytics_workspace_internet_ingestion_enabled = true
  log_analytics_workspace_internet_query_enabled     = true
}

module "id" {
  source           = "Azure/avm-res-managedidentity-userassignedidentity/azurerm"
  version          = "0.3.3"
  enable_telemetry = false

  name                = "id-${local.base_name}"
  resource_group_name = azurerm_resource_group.this.name
  location            = azurerm_resource_group.this.location
  tags                = local.tags
}



module "acr" {
  source           = "Azure/avm-res-containerregistry-registry/azurerm"
  version          = "0.4.0"
  enable_telemetry = false

  name                = replace("acr-${local.base_name}", "-", "")
  resource_group_name = azurerm_resource_group.this.name
  location            = azurerm_resource_group.this.location
  tags                = local.tags

  sku                        = "Basic"
  zone_redundancy_enabled    = false
  retention_policy_in_days   = null
  network_rule_bypass_option = "AzureServices"

  role_assignments = {
    "tf_AcrPush" = {
      role_definition_id_or_name = "AcrPush"
      principal_id               = data.azurerm_client_config.current.object_id
    }
    "id_AcrPull" = {
      role_definition_id_or_name = "AcrPull"
      principal_id               = module.id.principal_id
    }
  }
}

#resource "azurerm_container_app_environment" "this" {
#  name                = "cae-${local.base_name}"
#  resource_group_name = azurerm_resource_group.this.name
#  location            = azurerm_resource_group.this.location
#  tags                = local.tags

#  infrastructure_resource_group_name = "rg-cae-${local.base_name}"
#  infrastructure_subnet_id           = module.vnet.subnets["aca"].resource_id
#  # internal_load_balancer_enabled     = true

#  workload_profile {
#    name                  = "Consumption"
#    workload_profile_type = "Consumption"
#  }

#  logs_destination           = "log-analytics"
#  log_analytics_workspace_id = module.log_analytics.resource_id
#}


resource "azapi_resource" "cae" {
  type      = "Microsoft.App/managedEnvironments@2024-10-02-preview" # Latest api version is 2025-01-01; not yet supported by azapi with validation
  name      = "cae-${local.base_name}"
  parent_id = azurerm_resource_group.this.id
  location  = azurerm_resource_group.this.location
  tags      = local.tags

  body = {
    properties = {
      appLogsConfiguration = {
        destination = "azure-monitor"
      }
      infrastructureResourceGroup = "rg-cae-${local.base_name}"
      publicNetworkAccess = "Disabled"
      vnetConfiguration = {
        infrastructureSubnetId = module.vnet.subnets["aca"].resource_id
        internal               = true
      }

      workloadProfiles = [
        {
          name                = "Consumption",
          workloadProfileType = "Consumption"
        },
        {
          enableFips          = false
          maximumCount        = 5
          minimumCount        = 0
          name                = "memoryoptimzied"
          workloadProfileType = "E8"
        }
      ],
      zoneRedundant = false
    }
  }
}


resource "azurerm_monitor_diagnostic_setting" "env_diag" {
  name                       = "env-diagnostics-${local.base_name}"
  target_resource_id         = azapi_resource.cae.id
  log_analytics_workspace_id = module.log_analytics.resource_id

  # Logs you can collect
  enabled_log {
    category = "ContainerAppConsoleLogs"

  }
  enabled_log {
    category = "ContainerAppSystemLogs"
  }
  enabled_metric {
    category = "AllMetrics"

  }
}


#resource "null_resource" "push_image" { # Super hacky way to push the image to ACR (assumes az cli is present and authenticated)
#  triggers = {
#    image_name = local.image_name
#    image_tag  = local.image_tag
#    registry   = module.acr.name
#  }
#  provisioner "local-exec" {
#    command     = "az acr build -r ${module.acr.name} -t ${local.image_name}=${local.image_tag} ${path.module}/../"
#    interpreter = ["bash", "-c"]
#  }
#}

resource "azapi_resource" "caj" {                     # azurerm_container_app_job doesn't yet support identity in scale > rules
  type      = "Microsoft.App/jobs@2024-10-02-preview" # Latest api version is 2025-01-01; not yet supported by azapi with validation
  name      = "caj-${local.base_name}"
  parent_id = azurerm_resource_group.this.id
  location  = azurerm_resource_group.this.location
  tags      = local.tags

  identity {
    type = "UserAssigned"
    identity_ids = [
      module.id.resource_id
    ]
  }

  body = {
    properties = {
      environmentId       = azapi_resource.cae.id
      workloadProfileName = "Consumption"

      configuration = {
        replicaTimeout    = 18600 # This becomes "replicaTimeoutInSeconds" when bumping to apiVersion @2025-01-01
        replicaRetryLimit = 0

        triggerType = "Event"
        eventTriggerConfig = {
          parallelism            = 1
          replicaCompletionCount = 1
          scale = {
            minExecutions   = 0
            maxExecutions   = 10
            pollingInterval = 30
            rules = [{
              name = "queue"
              type = "azure-queue"
              metadata = {
                accountName = module.dls.name
                queueName   = basename(module.dls.queues["queue0"].id)
                queueLength = "1"
              }
              identity = module.id.resource_id
            }]
          }
        }
        registries = [{
          server   = module.acr.resource.login_server
          identity = module.id.resource_id
        }]
        identitySettings = [{
          identity = replace(module.id.resource_id, "resourceGroups", "resourcegroups")
          # lifecycle = "All"
        }]
      }

      template = {
        containers = [{
          name      = "ima-bi-verysmall"
          image     = "${local.registry}/${local.image_name}:${local.image_tag}"
          imageType = "ContainerImage" # This is removed when bumping to apiVersion @2025-01-01
          resources = {
            cpu    = 0.5
            memory = "1Gi"
          }
          env = [
            {
              name  = "STORAGE_ACCOUNT_NAME"
              value = module.dls.name
            },
            {
              name  = "QUEUE_NAME"
              value = basename(module.dls.queues["queue0"].id)
            },
            {
              name  = "AZURE_TENANT_ID"
              value = data.azurerm_client_config.current.tenant_id
            },
            {
              name  = "AZURE_CLIENT_ID"
              value = module.id.client_id
            }
          ]
        }]
      }
    }
  }

  #  depends_on = [null_resource.push_image]
}


resource "azapi_resource" "caj1" {                     # azurerm_container_app_job doesn't yet support identity in scale > rules
  type      = "Microsoft.App/jobs@2024-10-02-preview" # Latest api version is 2025-01-01; not yet supported by azapi with validation
  name      = "caj-2-${local.base_name}"
  parent_id = azurerm_resource_group.this.id
  location  = azurerm_resource_group.this.location
  tags      = local.tags

  identity {
    type = "UserAssigned"
    identity_ids = [
      module.id.resource_id
    ]
  }

  body = {
    properties = {
      environmentId       = azapi_resource.cae.id
      workloadProfileName = "memoryoptimzied"

      configuration = {
        replicaTimeout    = 18600 # This becomes "replicaTimeoutInSeconds" when bumping to apiVersion @2025-01-01
        replicaRetryLimit = 0

        triggerType = "Event"
        eventTriggerConfig = {
          parallelism            = 1
          replicaCompletionCount = 1
          scale = {
            minExecutions   = 0
            maxExecutions   = 10
            pollingInterval = 30
            rules = [{
              name = "queue"
              type = "azure-queue"
              metadata = {
                accountName = module.dls.name
                queueName   = basename(module.dls.queues["queue1"].id)
                queueLength = "1"
              }
              identity = module.id.resource_id
            }]
          }
        }
        registries = [{
          server   = module.acr.resource.login_server
          identity = module.id.resource_id
        }]
        identitySettings = [{
          identity = replace(module.id.resource_id, "resourceGroups", "resourcegroups")
          # lifecycle = "All"
        }]
      }

      template = {
        containers = [{
          name      = "ima-bi-medium"
          image     = "${local.registry}/${local.image_name}:${local.image_tag}"
          imageType = "ContainerImage" # This is removed when bumping to apiVersion @2025-01-01
          resources = {
            cpu    = 4
            memory = "32Gi"
          }
          env = [
            {
              name  = "STORAGE_ACCOUNT_NAME"
              value = module.dls.name
            },
            {
              name  = "QUEUE_NAME"
              value = basename(module.dls.queues["queue1"].id)
            },
            {
              name  = "AZURE_TENANT_ID"
              value = data.azurerm_client_config.current.tenant_id
            },
            {
              name  = "AZURE_CLIENT_ID"
              value = module.id.client_id
            }
          ]
        }]
      }
    }
  }

  #  depends_on = [null_resource.push_image]
}
# One more super hacky setup to push a test message to the queue
#locals {
#  test_process = "Extract_FRED_Data"
#  test_message = jsonencode({
#    ExecutionId = random_integer.test_execution_id.result
#    Process     = local.test_process
#  })
#}

#resource "random_integer" "test_execution_id" {
#  min = 10000
#  max = 99999
#  keepers = {
#    image_name = local.image_name
#    image_tag  = local.image_tag
#    process    = local.test_process
#  }
#}

#resource "null_resource" "test_message" {
#  triggers = {
#    test_execution_id = random_integer.test_execution_id.result
#  }
#  provisioner "local-exec" {
#    command     = "az storage message put --content '${local.test_message}' --queue-name ${basename(module.dls.queues["queue0"].id)} --account-name ${module.dls.name} --auth-mode login"
#    interpreter = ["bash", "-c"]
#  }
#
#  depends_on = [azapi_resource.caj]
#}
