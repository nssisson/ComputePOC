locals {
  virtual_network_address_space = "10.100.0.0/20"
}

module "nsg" {
  source           = "Azure/avm-res-network-networksecuritygroup/azurerm"
  version          = "0.4.0"
  enable_telemetry = false

  name                = "nsg-${local.base_name}"
  resource_group_name = azurerm_resource_group.this.name
  location            = azurerm_resource_group.this.location
  tags                = local.tags
}

module "ng" {
  source           = "Azure/avm-res-network-natgateway/azurerm"
  version          = "0.2.1"
  enable_telemetry = false

  name                = "ng-${local.base_name}"
  resource_group_name = azurerm_resource_group.this.name
  location            = azurerm_resource_group.this.location
  tags                = local.tags

  public_ips = {
    "pip" = { name = "pip-ng-${local.base_name}" }
  }
  public_ip_configuration = {
    zones        = []
    inherit_tags = true
  }
}

module "vnet" {
  source           = "Azure/avm-res-network-virtualnetwork/azurerm"
  version          = "0.8.1"
  enable_telemetry = false

  name                = "vnet-${local.base_name}"
  resource_group_name = azurerm_resource_group.this.name
  location            = azurerm_resource_group.this.location
  tags                = local.tags

  address_space = [local.virtual_network_address_space]

  subnets = {
    "aca" = {
      name             = "snet-aca-${local.base_name}"
      address_prefixes = [cidrsubnets(local.virtual_network_address_space, 1, 7)[0]]
      delegation = [{
        name               = "aca_delegation"
        service_delegation = { name = "Microsoft.App/environments" }
      }]
      network_security_group = { id = module.nsg.resource_id }
      nat_gateway            = { id = module.ng.resource_id }
    }
    "pep" = {
      name                   = "snet-pep-${local.base_name}"
      address_prefixes       = [cidrsubnets(local.virtual_network_address_space, 1, 7)[1]]
      network_security_group = { id = module.nsg.resource_id }
      nat_gateway            = { id = module.ng.resource_id }
    }
  }
}

module "privatelink" {
  source           = "Azure/avm-ptn-network-private-link-private-dns-zones/azurerm"
  version          = "0.10.1"
  enable_telemetry = false

  resource_group_creation_enabled = false
  resource_group_name             = azurerm_resource_group.this.name
  location                        = azurerm_resource_group.this.location
  tags                            = local.tags

  private_link_private_dns_zones = {
    for subresource in local.private_endpoints_enabled : subresource => {
      zone_name = subresource == "vault" ? "privatelink.vaultcore.azure.net" : "privatelink.${subresource}.core.windows.net"
    }
  }

  virtual_network_resource_ids_to_link_to = {
    "${module.vnet.name}" = {
      vnet_resource_id = module.vnet.resource_id
    }
  }
}
