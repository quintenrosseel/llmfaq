Please create an Azure Terraform template that satisfies the following request: 
- Authenticates to Azure with AZ login, using the subscription on that account
- Create a resource group, with a random element and the base name 'llm-faq-demo'
- Creates a storage account with a blob store container in that resource group 
- Creates a Neo4j database running on a simple VM  (using docker-compose of the latest community version)  running within a VNET, with IP whitelisting options through the network interface and network security group 
- An azure open AI instance, linked to the azure ML studio instance below
- An Azure machine learning instance linked to that same VNET in the same resource group, that can connect to both the Neo4j database and the blob store (as  data store and data asset) 
- Boilerplate Github repo with three scripts: one to scrape a particular webpage and save that content to the blob storage, one to populate the Neo4j database with data from the blob storage  using an embedding model (probably one from HuggingFace), one script that executes on-demand behind a rest endpoint, taking in the chat history, user prompt and transforms that with an embedding model (same model as earlier) to a vector as to retrieve similar content from the neo4j database, and then uses the retrieved chunks to prompt a large language model (the Azure Open AI service) 