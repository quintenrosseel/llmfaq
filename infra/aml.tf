# See https://docs.github.com/en/authentication/connecting-to-github-with-ssh/adding-a-new-ssh-key-to-your-github-account
# To add git to your AML workspace. 

# VARIABLES =============================================
# Key to connect to personal compute
variable "ssh_key" {
  default = "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAACAQDhRReNaJCWRWspPsviwX1IiEhD3+7IDmt6Da3eJ81rBZLus7IKf+JUxKNAm+8fX/Ovqdy/+fFHs9h0HK8kk/IWu2fU6jk4X1JDMO8J8UXfM8Y4v84xu2e/+pDvh3Cx64MHG5KzXwRxD8YgoMaIY4Dc/vStxc3+DWmzoT5IJ0KCOKeZJnmeqH29ck49fe/S120VPAp1R1nmISJ6B2RiWur8aEZfI0QuvO4jfMA9KskOO5bH3KsG1yCNqPKzEECCeGtVv5nF56BEPDckGlECKOXqnM7jT+mpzB9gBBy6uP9reLuie6rtsOk0kIZjPJhzSVravXcB3tyc4AxlXVzkz7LaT6J/DBA93jMg10sk22o/sIb/zySRlJCPI8ieu2tJs8ubxYt5ehznV+WHPsLmhmtY087zGRTQHxZUU3BCu/gya454my5ZPdg/lVV5fMdpjOnGGTMQlhoS+0yfhH4/kYctaBuOZqfyuuftN0oMRbG7c/a+WaTJUtpZDMnm6gYzqvzrEmuNDSpSaDdXRgHZ0QgIlFqsH/W6MraDUFoAh9x6CAreoHPKsUVUV1sq1qr5bIcGBDlp1XNIhjfB1Tm/nptvDhx3qbP5zXvY0rJgKfqh7T0e6zO+155BPsHmAVtAu3+fTNT6UK8Ks3PxGVki5TkJY9Ch+XKwyx6G0Mh7/K1NbQ== rossequ@cronos.be"
}

# APPLICATION INSIGHTS =============================================
# A default thing you need for AML
resource "azurerm_application_insights" "ai" {
  name                = "ai-${random_string.random.result}"
  location            = azurerm_resource_group.rg.location
  resource_group_name = azurerm_resource_group.rg.name
  application_type    = "web"
}

# CONTAINER REGISTRY =============================================
# For hosting ML models
resource "azurerm_container_registry" "acr" {
  name                = "acr${random_string.random.result}"
  resource_group_name = azurerm_resource_group.rg.name
  location            = azurerm_resource_group.rg.location
  sku                 = "Basic"  // Or choose a different SKU as needed
  admin_enabled       = true    // Set to true if you need admin access
}

# WORKSPACE =============================================
resource "azurerm_machine_learning_workspace" "ml_workspace" {
  name                    = "ml-workspace-${random_string.random.result}"
  location                = azurerm_resource_group.rg.location
  resource_group_name     = azurerm_resource_group.rg.name
  application_insights_id = azurerm_application_insights.ai.id
  key_vault_id            = azurerm_key_vault.kv.id
  storage_account_id      = azurerm_storage_account.storage.id
  container_registry_id   = azurerm_container_registry.acr.id
  public_network_access_enabled = true

  identity {
    type = "SystemAssigned"
  }
}

# PERSONAL COMPUTE CPU Q =============================================
resource "azurerm_machine_learning_compute_instance" "rossequ" {
  name                          = "rossequ"
  location                      = azurerm_resource_group.rg.location
  machine_learning_workspace_id = azurerm_machine_learning_workspace.ml_workspace.id
  virtual_machine_size          = "STANDARD_DS2_V2"
  authorization_type            = "personal"
  ssh {
    public_key = var.ssh_key
  }
  subnet_resource_id = azurerm_subnet.subnet.id
  description        = "personal compute"
  tags = {
    type = "personal"
  }
}

# PERSONAL COMPUTE GPU Q =============================================
# Not working due to quota limits as of now 

# resource "azurerm_machine_learning_compute_instance" "gpu_instance" {
#   name                          = "gpu-instance-name"  # Replace with your desired name
#   location                      = azurerm_resource_group.rg.location
#   machine_learning_workspace_id = azurerm_machine_learning_workspace.ml_workspace.id
#   virtual_machine_size          = "STANDARD_NV12s_v3"  # GPU-based VM size
#   authorization_type            = "personal"

#   ssh {
#     public_key = var.ssh_key
#   }

#   subnet_resource_id = azurerm_subnet.subnet.id
#   description        = "GPU compute instance"
#   tags = {
#     type = "gpu"
#   }
# }

# OPENAI =============================================
# Not explored yet. 

# # Azure Open AI Instance
# resource "azurerm_openai_instance" "openai" {
#   // Configuration for OpenAI instance
# }

