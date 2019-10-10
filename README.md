# Removing domain-wide visibility for Drive files using Cloud Functions
This is not an officially supported Google product, though support will be provided on a best-effort basis.

Copyright 2018 Google LLC

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    https://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

### Introduction

This sample Cloud Function code is designed to remove permissions from a Drive file where the file is visible across the entire domain. The Function is triggered against a Pub/Sub payload that contains Drive document metadata and sharing events that would prompt the Function to execute.

##### Google Cloud Products Used or Referenced:

- GSuite and Google Drive
- Google Cloud Functions
- Google Cloud Pub/Sub

##### General Architecture

The scope of this package **only pertains to parts 5 and 6** in the graphic below. For previous parts 1-4, please refer to this [repository](https://github.com/ocervell/terraform-google-gsuite-export) to get those elements set up.

<p align="center">
  <img src="https://storage.googleapis.com/cloud-function-edit-drive-permissions/github1.png" width="600px"/>
</p>

##### Definitions
- **GSuite Admin console** - Accessed from admin.google.com from a GSuite administrator account. Used to give API scopes to service accounts and set up security dashboarding and audit investigations.
- **Google Cloud Platform (GCP) project** - organizational unit within GCP that houses public cloud services such as VMs, logging and monitoring, data streaming, and serverless compute. “Projects” sit under an “Organization” that controls billing accounts and umbrella IAM policies for the domain.
- **GCP Console** - User interface to control GCP resources, accessed from console.cloud.google.com
- **Service Account** - an Identity and Access Management (IAM) role that is given specific permissions in order to fulfill an automated task, usually.
- **Stackdriver** - native logging, monitoring, and error reporting tool in GCP
- **Pub/Sub** (“Publisher/Subscriber”) - asynchronous, serverless messaging service, analogous to Apache Kafka. In this case, used to carry Stackdriver log entries to Cloud Functions.
- **Cloud Functions** - Serverless, autoscaling function-as-a-service that executes python or javascript code against a trigger, in this case, Pub/Sub messages

### Getting Started

##### Step 1: Create a GCP Project

In this step, we will create a GCP project (unless you already created one using while setting up this [Terraform repository](https://github.com/ocervell/terraform-google-gsuite-export)) and we will give the GSuite administrator the Project Owner role.

So let's create the project by going to [console.cloud.google.com](console.cloud.google.com) and sign in using your GSuite administrator's email. We will refer to this email as **{gsuite-admin-email}** from now on. You will need a billing account to enable the APIs in later steps.

From the sidebar menu, go to **IAM & admin** and click **IAM**.

<p align="center">
  <img src="https://storage.googleapis.com/cloud-function-edit-drive-permissions/github2.png" width="600px"/>
</p>

Click **"Add"**

<p align="center">
  <img src="https://storage.googleapis.com/cloud-function-edit-drive-permissions/github3.png" width="600px"/>
</p>

Give **{gsuite-admin-email}** the Project Owner role.

<p align="center">
  <img src="https://storage.googleapis.com/cloud-function-edit-drive-permissions/github4.png" width="600px"/>
</p>

##### Step 2: Enable APIs

Enable the following APIs in your GCP project:
- Admin SDK
- Google Drive
- Service Usage
- Resource Manager
- Stackdriver
- IAM
- IAM Service Account Credentials
- Token Service
- Pub/Sub
- Functions
- Compute Engine

<p align="center">
  <img src="https://storage.googleapis.com/cloud-function-edit-drive-permissions/github5.png" width="600px"/>
</p>

##### Step 3. Configure service account for the Cloud Functions

Go back to **IAM & admin** and click **Service Accounts**.

<p align="center">
  <img src="https://storage.googleapis.com/cloud-function-edit-drive-permissions/github6.png" width="600px"/>
</p>

Find the App Engine default service account. We will use **{service-account-name}** to reference it and it should end with "@appspot.gserviceaccount.com").

Create a JSON key and download the credential. We'll refer to this file as **{credential-file}**.

Give the service account domain-wide delegation, by first clicking **Edit** on the right-side options menu.

<p align="center">
  <img src="https://storage.googleapis.com/cloud-function-edit-drive-permissions/github7.png" width="600px"/>
</p>

Click **Show Domain-Wide Delegation** and enable.

<p align="center">
  <img src="https://storage.googleapis.com/cloud-function-edit-drive-permissions/github8.png" width="600px"/>
</p>

From the project dropdown at the top of the console, click the Organization that matches the domain you're working under and click **IAM & admin**.

Find the App Engine default service account and give it the “Service Account Token Creator” and "Project Editor" roles.

##### Step 4. Setup service account scopes in the GSuite admin console

Log into the [GSuite Admin console](admin.google.com) using **{gsuite-admin-email}**, then go to **Security** -> **Advanced Settings** -> **Manage API Scopes**

<p align="center">
  <img src="https://storage.googleapis.com/cloud-function-edit-drive-permissions/github9.png" width="600px"/>
</p>

<p align="center">
  <img src="https://storage.googleapis.com/cloud-function-edit-drive-permissions/github10.png" width="600px"/>
</p>

For **{service-account-name}**, set the following scopes by pasting the service account's Unique ID number, e.g., 100518674616449638338, in the name field and pasting this into the scopes field:
https://www.googleapis.com/auth/admin.directory.user,https://www.googleapis.com/auth/drive,https://www.googleapis.com/auth/iam

##### Step 5. Package the Zip file

You can retrieve this project's source code by running the following command:
`git clone https://github.com/google/cloud-function-edit-drive-permissions.git`

You need to update the following variables in the **main.py** file:
- Line 36: Change **{path-to-credential-file}**
- Line 39: Change **{gsuite-admin-email}**
- Line 68: Change **{OU}** if you want some Organizational Units to be exempt

From here, package the files in your current directory into a Zip file. At a minimum, this should include main.py, requirements.txt, and **{credential-file}**

Upload this Zip into a bucket using Cloud Storage. We'll reference this bucket as **{bucket-name}**.


##### Step 6. Create your Cloud Function

We will finally set up the Cloud Function that will strip domain-visibility from Drive documents.

Go to left menu and hit “Cloud Functions” then create a new Function.


Set **Trigger** to the Pub/Sub topic that is carrying the drive audit events. Again, this can be set up using this [Terraform](https://github.com/ocervell/terraform-google-gsuite-export).

Set Source Code to be from **ZIP from Cloud Storage** and link to the right **{bucket-name}**.

Click **Create**

To observe what’s happening, feel free to look at Logging from Stackdriver.
