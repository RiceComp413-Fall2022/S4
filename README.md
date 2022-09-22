# S4

Super Simple Storage Service

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
4. Setup environment variables:
   add the following line to the end of your venv/bin/activate script: <br>
   `export FILE_PATH=your_file_path_here`
   For example:
   `export FILE_PATH=/Users/ericy/Desktop`. Remember to add the '/' in front of the path, or else it will not work.

## Run the Server:

1. Run the server: `cd src && flask run`
2. To use see the Swagger documentation, visit the URL to the newly spun-up server (e.g. http://127.0.0.1:5000)

## Run Tests:

1. To run the unit tests, type `pytest` **in the test directory**.

## Endpoints
1. **generateKey:** Currently just generates a random key of length 16. Will remove later.
2. **GetObject:** Currently just gets a file from the specified local output path. This is the 
'export FILE_PATH' variable you have set. In the request parameters, you need to put a key called "Key" (with the uppercase K), and a "Value" as the name of your file (we will change this)
3. **PutObject:** Currently just puts a file as specified in the request body to the location specified in your 'export FILE_PATH' variable. The request parameters needs a key and a value. The value will be used later on to match files, but now it does nothing. The request body must be a file, and the value must be the actual file contents. You can do this easily in postman. Or you can do it in the swagger UI on 127.0.0.1:5000.
4. **ListObjects:** Currently just lists all of the objects in same directory that the FILE_PATH path lies. Will be modified to list just the objects in the DB? 