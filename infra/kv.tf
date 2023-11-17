# KEYVAULT =============================================
# Store secrets in AML 

resource "azurerm_key_vault" "kv" {
  name                = "kv-${random_string.random.result}"
  location            = azurerm_resource_group.rg.location
  resource_group_name = azurerm_resource_group.rg.name
  tenant_id           = data.azurerm_client_config.current.tenant_id
  sku_name            = "standard"

  network_acls {
    default_action = "Allow"
    bypass         = "AzureServices"
  }

access_policy {
    # Link to current logged in user
    tenant_id = data.azurerm_client_config.current.tenant_id
    object_id = data.azurerm_client_config.current.object_id

    key_permissions = [
      "Backup",
      "Create",
      "Decrypt",
      "Delete",
      "Encrypt",
      "Get",
      "Import",
      "List",
      "Purge",
      "Recover",
      "Restore",
      "Sign",
      "UnwrapKey",
      "Update",
      "Verify",
      "WrapKey"
    ]

    secret_permissions = [
      "Backup",
      "Delete",
      "Get",
      "List",
      "Purge",
      "Recover",
      "Restore",
      "Set"
    ]

    storage_permissions = [
        "Backup", 
        "Delete", 
        "DeleteSAS",
        "Get", 
        "GetSAS", 
        "List", 
        "ListSAS", 
        "Purge", 
        "Recover",
        "RegenerateKey", 
        "Restore", 
        "Set",
        "SetSAS", 
        "Update"
    ]
  }
}

resource "azurerm_key_vault_secret" "neo4j_url" {
  name         = "NEO4JURL"
  value        = "bolt://10.0.1.4/:7687"
  key_vault_id = azurerm_key_vault.kv.id
}

resource "azurerm_key_vault_secret" "neo4j_user" {
  name         = "NEO4JUSER"
  value        = "neo4j"
  key_vault_id = azurerm_key_vault.kv.id
}

resource "azurerm_key_vault_secret" "neo4j_password" {
  name         = "NEO4JPASSWORD"
  value        = "llmfaqdemo"
  key_vault_id = azurerm_key_vault.kv.id
}
