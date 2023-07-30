terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "=2.97.0"
    }
  }
}

provider "azurerm" {
  features {}
}

resource "azurerm_resource_group" "dknit-rg" {
  name     = "dknit-resources"
  location = "West Europe"
  tags = {
    environment = "dev"
  }
}

resource "azurerm_virtual_network" "dknit-vn" {
  name                = "dknit-vnet"
  resource_group_name = azurerm_resource_group.dknit-rg.name
  location            = azurerm_resource_group.dknit-rg.location
  address_space       = ["10.123.0.0/16"]

  tags = {
    environment = "dev"
  }

}

resource "azurerm_subnet" "dknit-subnet" {
  name                 = "dknit-subnet"
  resource_group_name  = azurerm_resource_group.dknit-rg.name
  virtual_network_name = azurerm_virtual_network.dknit-vn.name
  address_prefixes     = ["10.123.1.0/24"]
}

resource "azurerm_network_security_group" "dknit-nsg" {
  name                = "dknit-nsg"
  location            = azurerm_resource_group.dknit-rg.location
  resource_group_name = azurerm_resource_group.dknit-rg.name

  tags = {
    environment = "dev"
  }
}

resource "azurerm_network_security_rule" "dknit-dev-rule" {
  name                        = "dknit-dev-rule"
  priority                    = 100
  direction                   = "Inbound"
  access                      = "Allow"
  protocol                    = "Tcp"
  source_port_range           = "*"
  destination_port_range      = "*"
  source_address_prefix       = "*"
  destination_address_prefix  = "*"
  resource_group_name         = azurerm_resource_group.dknit-rg.name
  network_security_group_name = azurerm_network_security_group.dknit-nsg.name
}

resource "azurerm_subnet_network_security_group_association" "dknit-subnet-nsg" {
  subnet_id                 = azurerm_subnet.dknit-subnet.id
  network_security_group_id = azurerm_network_security_group.dknit-nsg.id
}

resource "azurerm_public_ip" "dknit-ip" {
  name                = "dknit-ip"
  location            = azurerm_resource_group.dknit-rg.location
  resource_group_name = azurerm_resource_group.dknit-rg.name
  allocation_method   = "Static"

  tags = {
    environment = "dev"
  }
}

resource "azurerm_network_interface" "dknit-nic" {
  name                = "dknit-nic"
  location            = azurerm_resource_group.dknit-rg.location
  resource_group_name = azurerm_resource_group.dknit-rg.name

  ip_configuration {
    name                          = "dknit-ip-config"
    subnet_id                     = azurerm_subnet.dknit-subnet.id
    private_ip_address_allocation = "Dynamic"
    public_ip_address_id          = azurerm_public_ip.dknit-ip.id
  }

  tags = {
    environment = "dev"
  }
}

resource "azurerm_linux_virtual_machine" "dknit-vm" {
  name                = "dknit-vm"
  resource_group_name = azurerm_resource_group.dknit-rg.name
  location            = azurerm_resource_group.dknit-rg.location
  size                = "Standard_B1s"
  admin_username      = "dknit"
  network_interface_ids = [
    azurerm_network_interface.dknit-nic.id,
  ]

  custom_data = filebase64("customdata.tpl")

  admin_ssh_key {
    username   = "dknit"
    public_key = file("~/.ssh/dknitazurekey.pub")
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
  computer_name                   = "dknit-vm"
  disable_password_authentication = true

  provisioner "local-exec" {
    command = templatefile("${var.host_os}-ssh-script.sh", {
      hostname     = self.public_ip_address,
      user         = "dknit",
      identityfile = "~/.ssh/dknitazurekey"
    })
    interpreter = var.host_os == "windows" ? ["Powershell", "-Command"] : ["bash", "-c"]
  }
  tags = {
    environment = "dev"
  }
}

data "azurerm_public_ip" "dknit-ip-data" {
  name                = azurerm_public_ip.dknit-ip.name
  resource_group_name = azurerm_resource_group.dknit-rg.name
}

output "public_ip_address" {
  value = "${azurerm_linux_virtual_machine.dknit-vm.name}: ${data.azurerm_public_ip.dknit-ip-data.ip_address}"
}