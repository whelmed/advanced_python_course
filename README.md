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
* Local Environment: Vagrant
* Production Environment: Google Cloud - Compute Engine
* Code Editor: Visual Studio Code
* Data Persistence: Cloud Firestore
* Blob storage: Cloud Storage
* ADD DATASET HERE



## Topic Selection
The goal of this course is to demonstrate how to use Python to build more complex applications than a simple hello world app. 
However, there's no limits on what that might cover. In the end, I searched online for what other people thought of when thinking about "advanced Python topics." Between the results I found online, and through my own experiences, I distilled the results down to a handful of topics that should help you to level up your code. :)

## Shape of The Problem
The last few projects I've worked on were across different industries. They had different requirements, used different programming languages, tools, platforms, etc. However, they shared the same basic shape. They all required some form of data ingestion process, and some form of user interface to consume the data. The application built in this course is going to be in the shape of data ingestion and consumption. 

## The Application's Reason for Being
The purpose of this application is to help us identify the most common topics mentioned by a select group of publications.
The way we'll accomplish this is to use natural language processing to perform entity extraction. 
...

## A Rough Lesson Plan

Exact plan may change.

* Sprint Planning 00: [5min] Introduction

* Sprint 01: [5min] Local Development Setup 
    * In this lesson we'll:
        * Start a Linux VM using Vagrant
        * Compile and install Python 3.8
        * Setup a virtual environment

* Sprint 02: [6min] Create a Text Processor
    * In this lesson we'll:
        * Create a centralized multiprocess logger
        * Install Spacy
        * Create an entity extraction process for text 

* Sprint 03: [8min] Create Message Queue with unit tests
    * In this lesson we'll:
        * Create a multiprocess aware, drainable queue
        * Use pytests to validate the functionality

* Sprint 04: [8min] Create Data Models, Create Shutdown Manager with unit tests, Stub Persistence Functions
    * In this lesson we'll:
        * Install Pydantic
        * Create Models
        * Create shutdown manager
            * Use pytests to validate the functionality
        * Create Persistence Function Stubs

* Sprint 05: [2 x 15min] Create Backend Process Manager, Configure Setup.py, Complete DB Persistence
    * In this lesson we'll:
        * Create a Worker process to handle input
        * Create a Saver process to handle database persistence
        * Create a main entrypoint
        * Create a setup.py file to install the app
        * Perform bug fixes
        * Complete DB Persistence

* Sprint 06: [11min] Create a Web Frontend for Ingesting Posts
    * In this lesson we'll:
        * Install FastAPI, Uvicorn, GUnicorn
        * Create an  HTTP endpoint to enqueue a Post(content: str, publication: str)
        * Implement a header-based API Key

* Sprint 07: [13min] Deploy App to Cloud VM
    * In this lesson we'll:
        * Install Supervisor
        * Review the configuration file
        * Run application with Supervisor
        * Create a 16 Core Cloud VM
        * Review the Deployment Process
        * Deploy
        * Verify Deployment

* Sprint 08: [14min] Exercising Deployed App
    * In this lesson we'll:
        * Review script for downloading a dataset
        * Review script for uploading Posts from dataset to Frontend
        * Install Typer, HTTPX
        * Create entrypoints for download and upload scripts
        * Process 100_000 Posts
        * Review processes with htop / strace
        * Identify a bug

* Sprint 08: [10min] Resolve Shutdown Bug
    * In this lesson we'll:
        * Resolve the bug 
        * Summarize what we've covered