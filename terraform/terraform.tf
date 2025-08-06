terraform {
  required_providers {
    azapi = {
      source  = "Azure/azapi"
      version = "~> 2.3.0"
    }
  }
}

provider "azurerm" {
  subscription_id = "24fd84c6-82b8-4b65-861a-1f6a2334b9f7"

  resource_providers_to_register = ["Microsoft.App"]
  storage_use_azuread            = true

  features {}
}

data "azurerm_client_config" "current" {}

data "http" "current_ip" {
  url = "https://api.ipify.org"
}
