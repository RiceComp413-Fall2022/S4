# S4

Super S3

## Team Members:

- Hunena Badat, hsb2@rice.edu
- John Shieh, jcs17@rice.edu
- Gavin Zhang, zz66@rice.edu
- Eric Yang, eyy1@rice.edu

## Pitch:
We want to create a distributed object storage system like S3 that focuses on the distributed aspects like reliability and scalability. Instead of creating an entire web front-end, we will be using REST API calls (GET and PUT) to upload and download files (we may or may not restrict the file types if there are certain difficulties). We will use 4 free AWS EC2 instances (1 free instance per team member) for distributed file storage and 1 web server that acts as a master. Users will communicate with the web server, and the server appropriately distributes the file(s) to the EC2 instances. Stretch goals include load balancing, fault tolerance, and scalability (make sure file download/upload doesn’t slow down with more instances, use fewer/more servers with changing demand). 

Proposal Doc: https://docs.google.com/document/d/e/2PACX-1vRGsQ7jpw3bz5lq5e-3cBRxnJzotZq034yJy0EUn0F8iKpqLDzQ3_fSGwiRQI6eYIMp1J3-XohiXuPR/pub

## First Time Setup:

1. Create a new virtual environment using Python 3.8.9:
   `python3 -m venv ./venv`
2. Activate virtual environment:
   `source ./venv/bin/activate`
3. Install requirements:
   `pip install -r requirements.txt`

## Run the Server:

1. To run the server, use `flask run`

## Run Tests:

1. To run the unit tests, use `pytest`


## Hello World TODO:

1. Use Python Flask web framework
2. Unit Tests
3. PUT and GET files, store them locally
