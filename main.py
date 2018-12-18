'''Copyright 2018 Google LLC

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    https://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.'''

import os
import cgi
import html
import json
import base64
import logging
import google.auth
import urllib.parse
from google.auth import iam
from google.cloud import pubsub_v1
from googleapiclient import discovery
from google.oauth2 import service_account
from google.auth.transport import requests
from google.auth.credentials import with_scopes_if_required
from google.auth._default import _load_credentials_from_file

#different Drive scopes that will be used in this Cloud Function
SCOPES = ["https://www.googleapis.com/auth/drive"]
SCOPES2 = ["https://www.googleapis.com/auth/admin.directory.user"]

#credentials file to include as part of Cloud Function package, e.g. 'credenials.json'
CREDENTIALS_PATH = '{path-to-credential-file}'

#email of GSuite admin, e.g., 'admin@domain.com'
ADMIN_EMAIL = '{gsuite-admin-email}'

def hello_pubsub(event, context):
    """Triggered from a message on a Cloud Pub/Sub topic.
    Args:
         event (dict): Event payload.
         context (google.cloud.functions.Context): Metadata for the event.
    """
    pubsub_message = base64.b64decode(event['data']).decode('utf-8')
    #Printing contents of decoded Pub/Sub payload to Stackdriver
    print(pubsub_message)
    #Taking Pub/Sub payload and creating JSON
    json_payload = json.loads(pubsub_message)
    parameters = json_payload["jsonPayload"]["parameters"]

    #Printing owner of Drive file to Stackdriver logs
    for i in parameters:
        if i["name"] == "owner":
            print("Found doc owner:%s" % i["value"])
            doc_owner = i["value"]

'''
    #Uncomment this block of code if you want this Cloud Function to skip certain OUs
    #Building Drive service object to obtain file owner's OU, if needed
    driveObj = build_service("admin","directory_v1",credentials_path=CREDENTIALS_PATH,user_email=ADMIN_EMAIL, scopes=SCOPES2)
    results = driveObj.users().get(userKey=doc_owner).execute()
    print(results['orgUnitPath'])
    OU = results['orgUnitPath']

    #If file owner's OU is exempt from this Cloud Function, use the if statement
    if OU != "/{OU}" and not OU.startswith('/{OU}/'):
'''
        for i in parameters:
             if i["name"] == "visibility" and (i["value"] == "people_within_domain_with_link" or i["value"] == "public_in_the_domain"):
                for p in parameters:
                    if p["name"] == "doc_id":
                        print("Found doc id:%s" % p["value"])
                        doc_id = p["value"]
                        #Removing permissions from this Drive file
                        delete_access(doc_id,doc_owner)

def delete_access(fileId,USER_EMAIL):
    driveObj = build_service("drive","v3",credentials_path=CREDENTIALS_PATH, user_email=USER_EMAIL, scopes=SCOPES)
    getpermissions = driveObj.permissions().list(fileId=fileId).execute()
    print(getpermissions['permissions'])

    for key in getpermissions['permissions']:
        print(key['type'])
        if key['type'] == "domain":
            permissionId = key['id']
            print(permissionId)
            chngObj = driveObj.permissions().delete(fileId = fileId,permissionId = permissionId).execute()
            print(chngObj)

logger = logging.getLogger(__name__)

_TOKEN_URI = 'https://accounts.google.com/o/oauth2/token'
_TOKEN_SCOPE = frozenset(['https://www.googleapis.com/auth/iam'])

def build_service(api, version, credentials_path=None, user_email=None, scopes=None):
    """Build and returns a service object.
    Allows delegation of GSuite permissions to the service account when the `user_email` argument is passed.
    Args:
      api (str): The Admin SDK API to use.
      version (str): The Admin SDK API version to use.
      credentials_path (str, optional): The path to the service account credentials.
      user_email (str): The email of the user. Needs permissions to access the Admin APIs.
      scopes (list, optional): A list of scopes to authenticate the request with.
    Returns:
      Google Service object.
    """
    if credentials_path is not None:
        logger.info("Getting credentials from file '%s' ...", credentials_path)
        credentials, _ = _load_credentials_from_file(credentials_path)
    else:
        logger.info("Getting default application credentials ...")
        credentials, _ = google.auth.default()

    if user_email is not None:  # make delegated credentials
        credentials = _make_delegated_credentials(
                credentials,
                user_email,
                scopes)

    return discovery.build(api, version, credentials=credentials)

def _make_delegated_credentials(credentials, user_email, scopes):
    """Make delegated credentials.
    Allows a service account to impersonate the user passed in `user_email`,
    using a restricted set of scopes.
    Args:
        credentials (service_account.Credentials): The service account credentials.
        user_email (str): The email for the user to impersonate.
        scopes (list): A list of scopes.
    Returns:
        service_account.Credentials: The delegated credentials
    """
    request = requests.Request()
    credentials = with_scopes_if_required(credentials, _TOKEN_SCOPE)
    credentials.refresh(request)
    email = credentials.service_account_email
    signer = iam.Signer(
        request,
        credentials,
        email)
    return service_account.Credentials(
        signer,
        email,
        _TOKEN_URI,
        scopes=scopes,
        subject=user_email)
