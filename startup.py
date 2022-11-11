import sys
import io
import time
import requests # pip install requests
import boto3 # pip install boto3[crt]

from fabric import Connection # pip install fabric

# TODO: dynamically create VPC (with subnet, etc.), keypair, security group
# TODO: automatic teardown

port = 8080
num_nodes = int(sys.argv[1])
if num_nodes < 2:
    print("At least 2 nodes are required for S4.")
    exit()
ec2 = boto3.resource('ec2')

instances = ec2.create_instances(
    ImageId='ami-03a56b7b6b25caf7b', # Custom AMI with dependencies preinstalled
    InstanceType='t2.micro', # 2 vCPU, 4 GiB memory
    KeyName='S4', # keypair for authentication
    MaxCount=num_nodes,
    MinCount=num_nodes,
    Placement={
        'AvailabilityZone': 'us-east-1b'
    },
    SecurityGroups=[
        'launch-wizard-1', # security group for firewall
    ],
    TagSpecifications=[
        {
            'ResourceType': 'instance',
            'Tags': [
                {
                    'Key': 'Name',
                    'Value': 'S4 Node' # instance name
                },
            ]
        },
    ],
    BlockDeviceMappings=[
        {
            'DeviceName': '/dev/xvda',
            'Ebs': {
                'VolumeSize': 8,
            }
        },
    ]
)

#The last ip in node_ips will be the main node, the rest will be workers
node_ips = []
for instance in instances:
    instance.wait_until_running()
    instance.load()
    node_ips.append(instance.public_ip_address)

node_urls = ["http://" + x + f":{port}/" for x in node_ips]
node_ips_f = io.StringIO("\n".join(node_urls))
print(node_urls)
def connect_retry(host, user, key):
    while True:
        try:
            c = Connection(
                host=host,
                user=user,
                connect_kwargs={
                    "key_filename": key,
                    "timeout": 5,
                    "banner_timeout": 5,
                    "auth_timeout": 5
                },
            )
            c.open()
            return c
        except Exception as e:
            print(f"Exception while connecting to host {host}: {e}")
            time.sleep(5)

for i, node in enumerate(node_ips):
    print(f"Connecting to node {node}, idx {i}")
    c = connect_retry(node, "ec2-user", "S4.pem")

    c.run("sudo yum update -y && sudo yum install tmux -y")
    c.run("cd S4 && git pull && source ./venv/bin/activate && pip install -r requirements.txt")
    c.put(node_ips_f, remote='S4/main/src/nodes.txt')
    if i < len(node_ips) - 1: # worker nodes
        c.run(f"tmux new-session -d \"cd S4 && source ./venv/bin/activate && cd worker && flask run --host=0.0.0.0 -p {port}\"", asynchronous=True)
    else: # main node
        c.run(f"tmux new-session -d \"cd S4 && source ./venv/bin/activate && cd main/src && flask run --host=0.0.0.0 -p {port}\"", asynchronous=True)
        
    c.close()

def test_node(node):
    success = True
    try:
        requests.get(f"http://{node}:{port}/HealthCheck", timeout=5)
    except:
        success = False
    return success

def wait_node(node):
    print(f"Waiting for {node}")
    while not test_node(node):
        time.sleep(5)

for node in node_ips:
    wait_node(node)

for idx, url in enumerate(node_urls):
    if idx < len(node_urls) - 1:
        print(f"Worker node: {url}")
    else:
        print(f"Main node: {url}")

# elb = boto3.client('elbv2')

# target_group = elb.create_target_group(
#     Name='cachecow-nodes',
#     Protocol='TCP',
#     Port=7070,
#     TargetType='instance',
#     VpcId='vpc-0b0b55be375992f99'
# )

# target_group_arn = target_group['TargetGroups'][0]['TargetGroupArn']

# targets = elb.register_targets(
#     TargetGroupArn=target_group_arn,
#     Targets=[{'Id': x.id, 'Port': 7070} for x in instances]
# )

# balancer = elb.create_load_balancer(
#     Name='cachecow-balancer',
#     Subnets=[
#         'subnet-0f380160653779f61'
#     ],
#     Scheme='internet-facing',
#     Type='network',
#     IpAddressType='ipv4'
# )

# balancer_arn = balancer['LoadBalancers'][0]['LoadBalancerArn']

# listener = elb.create_listener(
#     LoadBalancerArn=balancer_arn,
#     Protocol='TCP',
#     Port=7070,
#     DefaultActions=[
#         {
#             'Type': 'forward',
#             'TargetGroupArn': target_group_arn,
#             'ForwardConfig': {
#                 'TargetGroups': [
#                     {
#                         'TargetGroupArn': target_group_arn
#                     },
#                 ]
#             }
#         },
#     ],
# )

# elb.get_waiter('load_balancer_available').wait(LoadBalancerArns=[balancer_arn])

# elb_dns = elb.describe_load_balancers(LoadBalancerArns=[balancer_arn])['LoadBalancers'][0]['DNSName']

# wait_node(elb_dns)