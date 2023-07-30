# My playground to test VS Code Extensions and the latest AI assistants like GitHub CoPilot

# Learning Python through the creation of a data ingestion process.


## Source Code Structure

This source code is used as a part of the Cloud Academy Advanced Python development course.

The code is broken into multiple modules. 

/ingest is responsible for data ingestion, processing, and persistence.

/simultator is responsible for sending data to the ingestion front-end.

/web is responsible for serving up a web user interface.

## Software Used
* Python: 3.8.3
* OS: ubuntu/bionic64
* Daemon: Supervisord
* Local Environment: Vagrant + VirtualBox
* Production Environment: Google Cloud - Compute Engine
* Code Editor: Visual Studio Code
* Data Persistence: Cloud Firestore
* Blob storage: Cloud Storage


## Topic Selection
The goal of this course is to demonstrate how to use Python to build more complex applications than a simple hello world app. 
However, there's no limits on what that might cover. In the end, I searched online for what other people thought of when thinking about "advanced Python topics." Between the results I found online, and through my own experiences, I distilled the results down to a handful of topics that should help you to level up your code. :)


# Running the Web Server
data_storage="firestore" blob_storage="cloudstorage" blob_storage_bucket="advanced_python_cloud_academy" GOOGLE_APPLICATION_CREDENTIALS="/vagrant/service_account.json"  gunicorn -b "0.0.0.0:8080" -w 1 "web.main:create_app()" --timeout=60 

curl -XPOST http://127.0.0.1:8080/images -H "Authorization:8h45ty" 