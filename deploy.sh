#!/bin/sh

HOSTNAME=$1

gcloud compute ssh $HOSTNAME --zone=us-east4-c --command="sudo mkdir -p /usr/local/bin/data_ingestion/"
gcloud compute scp --recurse --zone=us-east4-c bootstrap.sh dist/ingest-0.0.1.tar.gz supervisord.conf "root@$HOSTNAME:/usr/local/bin/data_ingestion" 
gcloud compute ssh $HOSTNAME --zone=us-east4-c --command="bash /usr/local/bin/data_ingestion/bootstrap.sh"
gcloud compute ssh $HOSTNAME --zone=us-east4-c --command="~/venv/bin/pip install /usr/local/bin/data_ingestion/ingest-0.0.1.tar.gz"
gcloud compute ssh $HOSTNAME --zone=us-east4-c --command="~/venv/bin/python -m spacy download en_core_web_sm"