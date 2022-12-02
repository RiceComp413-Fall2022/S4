import sys
import json
import io
import time
import requests  # pip install requests
import boto3  # pip install boto3[crt]

from fabric import Connection  # pip install fabric

# TODO: dynamically create VPC (with subnet, etc.), keypair, security group
# TODO: automatic teardown

port = 8080
SECURITY_GROUP_NAME = 's4-security'

with open("nodes.txt") as f:
    worker_nodes = json.loads(f.read())

with open("scale_info.txt") as f:
    sys_info = f.readlines()

target_group_arn = sys_info[0][:-1]
main_url = sys_info[1][:-1]

num_nodes = len(worker_nodes)

ec2 = boto3.resource("ec2")


def get_vpc_and_subnet(ec2, zone):
    all_vpcs = list(ec2.vpcs.all())

    if len(all_vpcs) == 0:
        return None, None

    for subnet in all_vpcs[0].subnets.all():
        if subnet.availability_zone == zone:
            return all_vpcs[0].id, subnet.id

    return all_vpcs[0].id, None


vpc_id, subnet_id = get_vpc_and_subnet(ec2, "us-east-1b")

instances = ec2.create_instances(
    ImageId='ami-0b0dcb5067f052a63', # Amazon Linux 2 AMI (HVM) - Kernel 5.10, 64-bit (x86)
    # ImageId='ami-03a56b7b6b25caf7b', # Custom AMI with dependencies preinstalled
    InstanceType='t2.micro', # 2 vCPU, 4 GiB memory
    KeyName='S4', # keypair for authentication
    MaxCount=num_nodes,
    MinCount=num_nodes,
    Placement={"AvailabilityZone": "us-east-1b"},
    SecurityGroups=[
        SECURITY_GROUP_NAME, # security group for firewall
    ],
    TagSpecifications=[
        {
            "ResourceType": "instance",
            "Tags": [
                {"Key": "Name", "Value": "S4 Node"},  # instance name
            ],
        },
    ],
    BlockDeviceMappings=[
        {
            "DeviceName": "/dev/xvda",
            "Ebs": {
                "VolumeSize": 8,
            },
        },
    ],
)

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
                    "auth_timeout": 5,
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
    c.run("git clone https://github.com/RiceComp413-Fall2022/S4.git")
    c.run("cd S4 && python3 -m venv ./venv && source ./venv/bin/activate && pip install --upgrade pip && pip install -r requirements.txt")
    c.put(node_ips_f, remote='S4/main/src/nodes.txt')
    c.run(f"tmux new-session -d \"cd S4 && source ./venv/bin/activate && cd worker && flask run --host=0.0.0.0 -p {port}\"", asynchronous=True)
    
    c.close()


def test_node(node):
    success = True
    try:
        requests.get(
            f"http://{node}:{port}/HealthCheck",
            timeout=5,
            headers={"X-Api-Key": "gnohzoaboudibahsaminoacnagijizey"},
        )
    except:
        success = False
    return success


def wait_node(node):
    print(f"Waiting for {node}")
    while not test_node(node):
        time.sleep(5)


for node in node_ips:
    wait_node(node)

r = requests.post(
    main_url + "/ScaleUp",
    data={"nodes": json.dumps(node_urls)},
    headers={"X-Api-Key": "dapperdan"},
)
if r.status_code != 200:
    print(f"Error {r.status_code}")
    exit()

for idx, url in enumerate(node_urls):
    print(f"New Worker node: {url}")

elb = boto3.client("elbv2")

targets = elb.register_targets(
    TargetGroupArn=target_group_arn,
    Targets=[{"Id": x.id, "Port": port} for x in instances],
)

for i in range(len(instances)):
    instance = instances[i]
    worker_nodes["http://" + instance.public_ip_address + f":{port}/"] = instance.id

with open("nodes.txt", "w") as nodes_f:
    nodes_f.write(json.dumps(worker_nodes))
