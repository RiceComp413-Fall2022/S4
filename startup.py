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
ec2 = boto3.resource('ec2')

instances = ec2.create_instances(
    ImageId='ami-07cc33055027d7da8', # Custom AMI with dependencies preinstalled
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

#The last dns in node_dns will be the main node, the rest will be workers
node_dns = []

for instance in instances:
    instance.wait_until_running()
    instance.load()
    node_dns.append(instance.public_dns_name)

node_dns_f = io.StringIO("\n".join(x + f":{port}" for x in node_dns))

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

for i, node in enumerate(node_dns):
    c = connect_retry(node, "ec2-user", "S4.pem")

    c.run("sudo yum update -y")
    c.run("sudo yum install git tmux -y")

    c.run("git clone https://github.com/RiceComp413-Fall2022/S4.git")
    c.run("cd S4 && python3 -m venv ./venv && source ./venv/bin/activate && pip install -r requirements.txt")

    c.put(node_dns_f, remote='S4/main/src/nodes.txt')

    c.run("cd worker/src")

    if i < len(node_dns) - 1: # worker node
        c.run(f"./flask run --host=0.0.0.0 -p {port}")
    else: # main node
        c.run(f"cd ../../main/src && ./flask run --host=0.0.0.0 -p {port}")
        
    # TODO: update the main file to use nodes.txt
    c.close()

def test_node(node):
    success = True
    try:
        requests.get(f"http://{node}:{port}", timeout=5)
    except:
        success = False
    return success

def wait_node(node):
    print(f"Waiting for {node}")
    while not test_node(node):
        time.sleep(5)

for node in node_dns:
    wait_node(node)

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