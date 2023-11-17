# STOREAGE ACCOUNT (ML WORSPACE) =============================================
resource "azurerm_storage_account" "storage" {
  name                     = "storageaccount${random_string.random.result}"
  resource_group_name      = azurerm_resource_group.rg.name
  location                 = azurerm_resource_group.rg.location
  account_tier             = "Standard"
  account_replication_type = "LRS"
}

# STOREAGE CONTAINER =============================================
# For storing filesytem of azure machine learning service
resource "azurerm_storage_container" "container" {
  name                  = "blobcontainer"
  storage_account_name  = azurerm_storage_account.storage.name
  container_access_type = "private"
}


# # STOREAGE ACCOUNT WORSNFS SHARE =============================================
# resource "azurerm_storage_account" "storagenfs" {
#   name                     = "storageaccountnfs${random_string.random.result}"
#   resource_group_name      = azurerm_resource_group.rg.name
#   location                 = azurerm_resource_group.rg.location
#   account_tier             = "Standard"
#   account_kind             = "StorageV2"
#   account_replication_type = "LRS"
#   is_hns_enabled           = true
#   nfsv3_enabled            = true    # Persist storage from DB container 
  
#   network_rules {
#     ## Must be deny for NFS
#     default_action = "Deny"
#   }
# }

# # NFS FILE SHARE =============================================
# # https://registry.terraform.io/providers/hashicorp/azurerm/latest/docs/resources/storage_share
# # For persisting VM data
# resource "azurerm_storage_share" "nfs_share" {
#   name                 = "nfsshare"
#   storage_account_name = azurerm_storage_account.storagenfs.name
#   quota                = 100  # Set appropriate quota in GB

#   acl {
#     id = "everyone"
#     access_policy {
#       permissions = "rwdl"  # Read, write, delete, list permissions
#     }
#   }
# }
