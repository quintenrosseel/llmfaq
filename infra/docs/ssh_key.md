1. Open the Terminal: You can find it in Applications > Utilities > Terminal, or you can use Spotlight (Cmd + Space) to search for it.

2. Generate the SSH Key Pair:
Use the ssh-keygen command to generate a new SSH key pair. When you run the command, it will ask you where to save the new key. By default, it saves the key to the `~/.ssh/id_rsa` file. If you already have a key in that location, either choose a different file name or back up the existing key.

```bash
ssh-keygen -t rsa -b 4096 -C "rossequ@cronos.be"
```

Replace "your_email@example.com" with your email address. This email is just a label to help you identify the key.

3. Press Enter to Accept the Default File Location: When prompted, enter a passphrase for an additional layer of security or press Enter to continue without a passphrase.

4. Locate the SSH Public Key: Once the key pair is generated, you can find your SSH public key by navigating to the `~/.ssh` directory and looking for a file named `id_rsa.pub`. This is the key you will use in your Terraform configuration.

5. Copy the Public Key:
To copy the contents of your public key to the clipboard, use the pbcopy command:

```bash
pbcopy < ~/.ssh/id_rsa.pub
Now you can paste this key into your Terraform configuration or wherever else it's needed.
```

6. Using the Key in Terraform
In your Terraform configuration, for the admin_ssh_key block, you can directly reference this file:

```hcl
Copy code
admin_ssh_key {
  username   = "adminuser"
  public_key = file("~/.ssh/id_rsa.pub")
}
```

**Security Note**
Keep your private key (id_rsa) secure and never share it. The public key (id_rsa.pub) is what you can safely distribute to systems (like your Azure VM) for SSH access.



# Connecting to the vm
```zsh
    ssh -i ~/.ssh/id_rsa adminuser@20.111.32.34
```