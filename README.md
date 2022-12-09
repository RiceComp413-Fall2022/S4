# S4

Super Simple Storage Service

## Team Members:

- Hunena Badat, hsb2@rice.edu, nenab2501@gmail.com
- John Shieh, jcs17@rice.edu, thejohnshieh@gmail.com
- Gavin Zhang, zz66@rice.edu, gavin2600@gmail.com
- Eric Yang, eyy1@rice.edu, ericy848@gmail.com

Links: [Proposal Doc](https://docs.google.com/document/d/e/2PACX-1vRGsQ7jpw3bz5lq5e-3cBRxnJzotZq034yJy0EUn0F8iKpqLDzQ3_fSGwiRQI6eYIMp1J3-XohiXuPR/pub), Google Drive
## First Time Setup:

1. Create a new virtual environment using Python 3.8.9:
   `python3 -m venv ./venv`
2. Activate virtual environment:
   `source ./venv/bin/activate`
3. Install requirements:
   `pip install -r requirements.txt`
4. Setup dashboard:
   From the dashboard folder, install dashboard requirements:
   `npm i`
   
## Run on AWS:
### Setup:
1. Set up AWS credentials and region: https://docs.aws.amazon.com/sdk-for-java/v1/developer-guide/setup-credentials.html (region should be us-east-1 by default). This can also be done with `aws configure` if the AWS CLI is set up.
2. Copy S4.pem into the top-level directory, at the same level as startup.py.
### Start nodes:
1. Run the startup script: `python3 startup.py <# nodes>` where the number of nodes is > 1. This will start one main node and the rest will be worker nodes.
2. Once the script is finished, it will output the URL for the load balancer. To interact with the endpoints via Swagger, visit that URL.
### Scale Up:
1. After running the startup script, run the scale_up script: `python3 scale_up.py`. This will double the number of current nodes, using information on the main node and current worker nodes stored in the files scale_info.txt and nodes.txt
2. After the script is complete, it will output the URLs of the new worker nodes.
### Scale Down:
1. After running the startup script, run the scale_down script: `python3 scale_down.py`. This will halve the number of currently running workers, if there are more than 3 workers running. Workers no longer needed will be removed from the load balancer and terminated.
2. After the script is complete, it will output the URL of the worker nodes that were terminated.
### Cleanup:
1. After running the startup script and any of the other scripts, clean up the resources with `python3 cleanup.py`. This will delete the load balancer, target group, security group, and terminate all instances.

## Run the Dashboard:

1. After starting the server, from the dashboard folder:
   `npm start`

## Run Tests:

1. To run the unit tests, type `pytest` **in the test directory**.
