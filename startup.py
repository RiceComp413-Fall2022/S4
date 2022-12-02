import sys
import io
import time
import requests # pip install requests
import boto3 # pip install boto3[crt]
import json
import shutil

from fabric import Connection # pip install fabric

PORT_NUM = 8080
SECURITY_GROUP_NAME = 's4-security'

num_nodes = int(sys.argv[1])
if num_nodes < 2:
    print("At least 2 nodes are required for S4.")
    exit()
ec2_resource = boto3.resource('ec2')
ec2_client = boto3.client('ec2')

def get_vpc_and_subnet(ec2, zone):
    default_vpc = None
    for vpc in ec2.vpcs.all():
        if vpc.is_default:
            default_vpc = vpc

    if default_vpc is None:
        return None, None

    for subnet in default_vpc.subnets.all():
        if subnet.availability_zone == zone:
            return default_vpc.id, subnet.id

    return default_vpc.id, None

vpc_id, subnet_id = get_vpc_and_subnet(ec2_resource, 'us-east-1b')

def security_group_exists():
    for group in ec2_client.describe_security_groups()['SecurityGroups']:
        if group['GroupName'] == SECURITY_GROUP_NAME:
            return True
    return False

if not security_group_exists():
    security_group = ec2_resource.create_security_group(
        GroupName=SECURITY_GROUP_NAME,
        Description='Security group for S4',
        VpcId=vpc_id,
    )

    security_group.authorize_ingress(
        IpPermissions=[
                {
                    'IpProtocol': 'tcp',
                    'FromPort': PORT_NUM,
                    'ToPort': PORT_NUM,
                    'IpRanges': [
                        {
                            'CidrIp': '0.0.0.0/0'
                        }
                    ]
                },
                {
                    'IpProtocol': 'tcp',
                    'FromPort': 80,
                    'ToPort': 80,
                    'IpRanges': [
                        {
                            'CidrIp': '0.0.0.0/0'
                        }
                    ]
                },
                {
                    'IpProtocol': 'tcp',
                    'FromPort': 443,
                    'ToPort': 443,
                    'IpRanges': [
                        {
                            'CidrIp': '0.0.0.0/0'
                        }
                    ]
                },
                {
                    'IpProtocol': 'tcp',
                    'FromPort': 22,
                    'ToPort': 22,
                    'IpRanges': [
                        {
                            'CidrIp': '0.0.0.0/0'
                        }
                    ]
                }
            ]
    )

instances = ec2_resource.create_instances(
    ImageId='ami-0b0dcb5067f052a63', # Amazon Linux 2 AMI (HVM) - Kernel 5.10, 64-bit (x86)
    # ImageId='ami-03a56b7b6b25caf7b', # Custom AMI with dependencies preinstalled
    InstanceType='t2.micro', # 2 vCPU, 4 GiB memory
    KeyName='S4', # keypair for authentication
    MaxCount=num_nodes,
    MinCount=num_nodes,
    Placement={
        'AvailabilityZone': 'us-east-1b'
    },
    SecurityGroups=[
        SECURITY_GROUP_NAME, # security group for firewall
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
node_url_to_instance_id = {}
main_instance_id = ""
for i in range(len(instances)):
    instance = instances[i]
    instance.wait_until_running()
    instance.load()
    node_ips.append(instance.public_ip_address)
    if i < len(instances) - 1: 
        node_url_to_instance_id["http://" + instance.public_ip_address + f":{PORT_NUM}/"] = instance.id
    else:
        main_instance_id = instance.id

node_urls = ["http://" + x + f":{PORT_NUM}/" for x in node_ips]
print(node_urls)
worker_node_urls = node_urls[:-1]
main_node_url = node_urls[-1]
node_ips_f = io.StringIO("\n".join(worker_node_urls))


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

    c.run("sudo yum update -y && sudo yum install git tmux -y")
    c.run("git clone -b dashboard https://github.com/RiceComp413-Fall2022/S4.git")
    c.run("cd S4 && python3 -m venv ./venv && source ./venv/bin/activate && pip install --upgrade pip && pip install -r requirements.txt")
    c.put(node_ips_f, remote='S4/main/src/nodes.txt')
    if i < len(node_ips) - 1: # worker nodes
        c.run(f"tmux new-session -d \"cd S4 && source ./venv/bin/activate && cd worker && flask run --host=0.0.0.0 -p {PORT_NUM}\"", asynchronous=True)
    else: # main node
        c.run(f"tmux new-session -d \"cd S4 && source ./venv/bin/activate && cd main/src && flask run --host=0.0.0.0 -p {PORT_NUM}\"", asynchronous=True)
        
    c.close()

def test_node(node):
    success = True
    try:
        requests.get(f"http://{node}:{PORT_NUM}/HealthCheck", timeout=5)
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

elb = boto3.client('elbv2')

target_group = elb.create_target_group(
    Name='s4-nodes',
    Protocol='TCP',
    Port=PORT_NUM,
    TargetType='instance',
    VpcId=vpc_id
)

target_group_arn = target_group['TargetGroups'][0]['TargetGroupArn']

targets = elb.register_targets(
    TargetGroupArn=target_group_arn,
    Targets=[{'Id': x.id, 'Port': PORT_NUM} for idx, x in enumerate(instances) if idx < len(instances) - 1]
)

balancer = elb.create_load_balancer(
    Name='s4-balancer',
    Subnets=[
        subnet_id
    ],
    Scheme='internet-facing',
    Type='network',
    IpAddressType='ipv4'
)

balancer_arn = balancer['LoadBalancers'][0]['LoadBalancerArn']

listener = elb.create_listener(
    LoadBalancerArn=balancer_arn,
    Protocol='TCP',
    Port=PORT_NUM,
    DefaultActions=[
        {
            'Type': 'forward',
            'TargetGroupArn': target_group_arn,
            'ForwardConfig': {
                'TargetGroups': [
                    {
                        'TargetGroupArn': target_group_arn
                    },
                ]
            }
        },
    ],
)

elb.get_waiter('load_balancer_available').wait(LoadBalancerArns=[balancer_arn])

def test_lb(node):
    success = True
    try:
        requests.get(f"http://{node}:{PORT_NUM}", timeout=5)
    except:
        success = False
    return success

def wait_lb(node):
    print(f"Waiting for {node}")
    while not test_lb(node):
        time.sleep(5)

def get_security_group_id_name():
    for group in ec2_client.describe_security_groups()['SecurityGroups']:
        if group['GroupName'] == SECURITY_GROUP_NAME:
            return group['GroupId'], group['GroupName']
        
elb_dns = elb.describe_load_balancers(LoadBalancerArns=[balancer_arn])['LoadBalancers'][0]['DNSName']
wait_lb(elb_dns)
elb_arn = elb.describe_load_balancers(LoadBalancerArns=[balancer_arn])['LoadBalancers'][0]['LoadBalancerArn']
group_id, group_name = get_security_group_id_name()

with open("nodes.txt", "w") as nodes_f:
    nodes_f.write(json.dumps(node_url_to_instance_id))
with open("scale_info.txt", "w") as scale_f:
    scale_f.write(f"{target_group_arn}\n{main_node_url}\nhttp://{elb_dns}:{PORT_NUM}\n{elb_arn}\n{group_id}\n{group_name}\n{main_instance_id}")

shutil.copyfile("./nodes.txt", "./dashboard/src/notes.txt")

print(f"Load balancer: http://{elb_dns}:{PORT_NUM}")