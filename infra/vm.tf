# VIRTUAL MACHINE =============================================
# Hosts Neo4j, Neodash 
# See setup script neo4j_setup.sh
# Links to a private/public key that you need to add in order to SSH into the VM. 
# See ssh_key.md for more info. 

# Get endpoint of NFS fileshare 
# locals {
#   nfs_share_endpoint = "azurerm_storage_account.storagenfs.primary_file_host/nfsshare"
# }

resource "azurerm_linux_virtual_machine" "vm" {
    name                = "vm-${random_string.random.result}"
    resource_group_name = azurerm_resource_group.rg.name
    location            = azurerm_resource_group.rg.location
    size                = "Standard_F8"  // Choose the appropriate VM size
    admin_username      = "adminuser"
    network_interface_ids = [azurerm_network_interface.ni.id]

    admin_ssh_key {
        username   = "adminuser"
        public_key = file("~/.ssh/id_rsa.pub")  
    }

    os_disk {
        caching              = "ReadWrite"
        storage_account_type = "Standard_LRS"
    }

    source_image_reference {
        publisher = "Canonical"
        offer     = "UbuntuServer"
        sku       = "18.04-LTS"
        version   = "latest"
    }

    provisioner "file" {
        source      = "neo4j_setup.sh"
        destination = "/tmp/neo4j_setup.sh"

        connection {
            type        = "ssh"
            user        = "adminuser"
            private_key = file("~/.ssh/id_rsa") // Private key corresponding to id_rsa.pub  
            host        = self.public_ip_address
        }
    }

    provisioner "remote-exec" {
        inline = [
            # When uncommenting as below, the disk actually runs as expected. 
            # "DISK=$(lsblk -np | grep -v 'rom\\|part\\|loop' | tail -n1 | awk '{print $1}')", # Mount Disk share code 
            # "sudo mkfs -t ext4 $DISK", 
            # "sudo mkdir -p /mnt/neo4jmount",
            # "sudo mount $DISK /mnt/neo4jmount",
            # "echo '$DISK /mnt/neo4jmount ext4 defaults,nofail 0 2' | sudo tee -a /etc/fstab",
            # "sudo apt-get install -y nfs-common",  # Mount NFS share code 
            # "sudo mkdir -p /mnt/nfs-share",
            # "sudo mount -t nfs ${local.nfs_share_endpoint} /mnt/nfs-share",
            # "echo '${local.nfs_share_endpoint} /mnt/nfs-share nfs defaults 0 0' | sudo tee -a /etc/fstab",
            "sudo chmod +x /tmp/neo4j_setup.sh", # Setup Neo4j
            "sudo /tmp/neo4j_setup.sh"
        ]

        connection {
            type        = "ssh"
            user        = "adminuser"
            private_key = file("~/.ssh/id_rsa") // Private key corresponding to id_rsa.pub  
            host        = self.public_ip_address
        }
    }
}

# DISK OF VM =============================================
# Uncommented for now, as this approach doesn't seem to work. 
# resource "azurerm_managed_disk" "volume" {
#   name                 = "managed-disk"
#   location             = azurerm_resource_group.rg.location
#   resource_group_name  = azurerm_resource_group.rg.name
#   storage_account_type = "Standard_LRS"
#   create_option        = "Empty"
#   disk_size_gb         = 100 // Size in GB
# }

# resource "azurerm_virtual_machine_data_disk_attachment" "volume" {
#   managed_disk_id    = azurerm_managed_disk.volume.id
#   virtual_machine_id = azurerm_linux_virtual_machine.vm.id
#   lun                = "10" // Logical Unit Number
#   caching            = "ReadWrite"
# }
