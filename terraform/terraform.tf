terraform {
  required_providers {
    azapi = {
      source  = "Azure/azapi"
      version = "~> 2.3.0"
    }
  }
}

provider "azurerm" {
  # subscription_id = "<SUBSCRIPTION_ID>"

  resource_providers_to_register = ["Microsoft.App"]
  storage_use_azuread            = true

  features {}
}

data "azurerm_client_config" "current" {}

data "http" "current_ip" {
  url = "https://api.ipify.org"
}
