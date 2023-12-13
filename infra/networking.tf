# VARIABLES =============================================
variable "whitelisted_ips" {
  type    = list(string)
  default = [
    "91.180.55.182",     # Kroonlaan 222
    "91.182.220.66",    # Neerijse Steenweg 36
    "165.225.12.117",    # Atlas Copco, Wilrijk
    "81.164.217.80",     # Benoit's home (Maud)
    "77.109.89.232",      # Benoit's home (Antwerpse Steenweg)
    "94.143.189.243",      # Brussels Office  
    "149.154.233.132",   # Yann's IP addres
    # "213.246.223.34" # Billit's IP
  ]  # You can add more IPs to this list
}

# VM SUBNET =============================================
resource "azurerm_virtual_network" "vnet" {
  name                = "llm-vnet"
  address_space       = ["10.0.0.0/16"]
  location            = azurerm_resource_group.rg.location
  resource_group_name = azurerm_resource_group.rg.name
}

# SUBNET =============================================
resource "azurerm_subnet" "subnet" {
  name                 = "llm-subnet"
  resource_group_name  = azurerm_resource_group.rg.name
  virtual_network_name = azurerm_virtual_network.vnet.name
  address_prefixes     = ["10.0.1.0/24"]
}


# PUBLIC IP =============================================
resource "azurerm_public_ip" "public_ip" {
  name                = "publicip-${random_string.random.result}"
  location            = azurerm_resource_group.rg.location
  resource_group_name = azurerm_resource_group.rg.name
  allocation_method   = "Static"
  sku                 = "Basic"
}

# NETWORK INTERFACE (NI) =============================================
resource "azurerm_network_interface" "ni" {
  name                 = "llm-ni"
  resource_group_name  = azurerm_resource_group.rg.name
  location             = azurerm_resource_group.rg.location

  ip_configuration {
    name                          = "ipconfig1"
    subnet_id                     = azurerm_subnet.subnet.id
    private_ip_address_allocation = "Static"
    private_ip_address            = "10.0.1.4"  # Specify a valid IP address within the subnet range
    public_ip_address_id          = azurerm_public_ip.public_ip.id // Uncomment if you need a public IP
  }
}

# NETWORK SECURITY GROUPS (NSG) & SECURITY RULES =============================================
resource "azurerm_network_security_group" "nsg" {
  name                = "nsg-${random_string.random.result}"
  location            = azurerm_resource_group.rg.location
  resource_group_name = azurerm_resource_group.rg.name

  # INBOUND HTTP NEO4J CONNECTIONS FOR EVERY WHITELISTED IP
  dynamic "security_rule" {
    for_each = {for idx, val in var.whitelisted_ips : idx => val}
    iterator = ip

    content {
      name                       = "Neo4jHTTPInbound-${ip.key}"
      priority                   = 100 + ip.key
      direction                  = "Inbound"
      access                     = "Allow"
      protocol                   = "*"
      source_port_range          = "*"
      destination_port_range     = "7474"
      source_address_prefix      = ip.value
      destination_address_prefix = "*"
    }
  }

  # INBOUND BOLT NEO4J CONNECTIONS FOR EVERY WHITELISTED IP
  dynamic "security_rule" {
    for_each = {for idx, val in var.whitelisted_ips : idx => val}
    iterator = ip

    content {
      name                       = "Neo4jBoltInbound-${ip.key}"
      priority                   = 110 + ip.key
      direction                  = "Inbound"
      access                     = "Allow"
      protocol                   = "*"
      source_port_range          = "*"
      destination_port_range     = "7687"
      source_address_prefix      = ip.value
      destination_address_prefix = "*"
    }
  }

 # INBOUND NEODASH CONNECTIONS FOR EVERY WHITELISTED IP
  dynamic "security_rule" {
    for_each = {for idx, val in var.whitelisted_ips : idx => val}
    iterator = ip

    content {
      name                       = "NeodashHttpInbound-${ip.key}"
      priority                   = 210 + ip.key
      direction                  = "Inbound"
      access                     = "Allow"
      protocol                   = "*"
      source_port_range          = "*"
      destination_port_range     = "5005"
      source_address_prefix      = ip.value
      destination_address_prefix = "*"
    }
  }

 # OUTBOUND NEODASH CONNECTIONS FOR EVERY WHITELISTED IP
  dynamic "security_rule" {
    for_each = {for idx, val in var.whitelisted_ips : idx => val}
    iterator = ip

    content {
      name                       = "NeodashHttpOutbound-${ip.key}"
      priority                   = 310 + ip.key
      direction                  = "Outbound"
      access                     = "Allow"
      protocol                   = "*"
      source_port_range          = "*"
      destination_port_range     = "5005"
      source_address_prefix      = "*"
      destination_address_prefix = "*" // Any
    }
  }

  # OUTBOUND BOLT NEO4J CONNECTIONS
  security_rule {
    name                       = "Neo4jBoltOutbound"
    priority                   = 110
    direction                  = "Outbound"
    access                     = "Allow"
    protocol                   = "*"
    source_port_range          = "*"
    destination_port_range     = "7687"
    source_address_prefix      = "*"
    destination_address_prefix = "*" // Any
    // destination_address_prefix = "10.0.0.0/16" // VNET address space, doesn't work
  }
}


# NETWORK SECURITY GROUPS RULES =============================================

# INBOUND/OUTBOUND SSH CONNECTIONS FOR EVERY WHITELISTED IP 
resource "azurerm_network_security_rule" "nsg_rule" {
  for_each = {for idx, ip in var.whitelisted_ips : tostring(idx) => ip}

  name                        = "SSH-${each.key}"
  priority                    = 1001 + tonumber(each.key)
  direction                   = "Inbound"
  access                      = "Allow"
  protocol                    = "Tcp"
  source_port_range           = "*"
  destination_port_range      = "22"
  source_address_prefix       = "${each.value}/32"
  destination_address_prefix  = "*"
  resource_group_name         = azurerm_resource_group.rg.name
  network_security_group_name = azurerm_network_security_group.nsg.name
}

# NI-NSG ASSOCIATION =============================================
resource "azurerm_network_interface_security_group_association" "nsg_association" {
  network_interface_id      = azurerm_network_interface.ni.id
  network_security_group_id = azurerm_network_security_group.nsg.id
}


