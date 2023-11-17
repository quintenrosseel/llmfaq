See https://learn.microsoft.com/en-us/azure/machine-learning/concept-train-model-git-integration?view=azureml-api-2&tabs=python
# Step 1 
Go to your user folder and open a terminal. 

# Step 2
Run 
`ssh-keygen -t rsa -b 4096 -C "quinten.rosseel@hotmail.com"`
Press enter twice (no passport, default name)

# Step 3
Execute
`cat ~/.ssh/id_rsa.pub`

And add this to your github account, on https://github.com/settings/keys. 

# Step 4 
Add key to ssh-agent, https://docs.github.com/en/authentication/connecting-to-github-with-ssh/generating-a-new-ssh-key-and-adding-it-to-the-ssh-agent

Start the ssh-agent in the background.
`eval "$(ssh-agent -s)"`

# Step 5
Add ssh config on `sudo nano ~/.ssh/config`
Paste the following in the config file
```sh
Host github.com
  AddKeysToAgent yes
  IdentityFile ~/.ssh/id_rsa
```

# Step 6
Add to keychain
`ssh-add ~/.ssh/id_rsa`
Identity should be added. (appears)


# Step 7
Clone the git, it can be that you have to close & reopen the terminal to make sure that it works. 
`git clone git@github.com:quintenrosseel/llmfaq.git`