
import os
import sys
from box_sdk_gen import BoxClient, BoxDeveloperTokenAuth

token = "dummy_token"
auth = BoxDeveloperTokenAuth(token=token)
client = BoxClient(auth=auth)

print("Attributes of client.files:")
print(dir(client.files))

print("\nAttributes of client.downloads:")
try:
    print(dir(client.downloads))
except:
    print("No client.downloads")
