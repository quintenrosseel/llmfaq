# provider Configuration
provider "azurerm" {
  features {}
}

# Authentication and Subscription Setup (AZ Login)
data "azurerm_client_config" "current" {}

# Create Resource Group
resource "random_string" "random" {
  length  = 8
  special = false
  upper   = false
  numeric = false
  lower   = true
}

resource "azurerm_resource_group" "rg" {
  name     = "llm-faq-demo-${random_string.random.result}"
  location = "France Central"
}

