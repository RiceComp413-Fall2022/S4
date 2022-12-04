import sys
import json
import io
import time
import requests  # pip install requests
import boto3  # pip install boto3[crt]
import shutil

from fabric import Connection  # pip install fabric

# TODO: dynamically create VPC (with subnet, etc.), keypair, security group
# TODO: automatic teardown

port = 8080


with open("nodes.txt") as f:
    worker_nodes = json.loads(f.read())

with open("scale_info.txt") as f:
    sys_info = f.readlines()

target_group_arn = sys_info[0][:-1]
main_url = sys_info[1][:-1]

ec2 = boto3.resource("ec2")

r = requests.post(main_url + "/ScaleDown", headers={"X-Api-Key": "dapperdan"})
if r.status_code != 200:
    print(f"Error {r.status_code}")
    exit()

result = r.json()
removed_nodes = json.loads(result["nodes"])
print(removed_nodes)


def get_vpc_and_subnet(ec2, zone):
    all_vpcs = list(ec2.vpcs.all())

    if len(all_vpcs) == 0:
        return None, None

    for subnet in all_vpcs[0].subnets.all():
        if subnet.availability_zone == zone:
            return all_vpcs[0].id, subnet.id

    return all_vpcs[0].id, None


vpc_id, subnet_id = get_vpc_and_subnet(ec2, "us-east-1b")


for idx, url in enumerate(removed_nodes):
    print(f"Worker Node Cleared: {url}")

elb = boto3.client("elbv2")

instance_ids = []
for rmv_node in removed_nodes:
    instance_ids.append(worker_nodes[rmv_node])
    del worker_nodes[rmv_node]

# remove from load balancer
targets = elb.deregister_targets(
    TargetGroupArn=target_group_arn,
    Targets=[{"Id": x, "Port": port} for x in instance_ids],
)

# terminate instances
ec2.instances.filter(InstanceIds=instance_ids).terminate()

# remove terminated nodes from nodes.txt
with open("nodes.txt", "w") as nodes_f:
    nodes_f.write(json.dumps(worker_nodes))

shutil.copyfile("./nodes.txt", "./dashboard/src/nodes.txt")
