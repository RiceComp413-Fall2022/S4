import sys
import json
import io
import time
import requests # pip install requests
import boto3 # pip install boto3[crt]

from fabric import Connection # pip install fabric

# TODO: dynamically create VPC (with subnet, etc.), keypair, security group
# TODO: automatic teardown

PORT_NUM = 8080

with open("nodes.txt") as f:
    worker_nodes = json.loads(f.read())

with open("scale_info.txt") as f:
    sys_info = f.readlines()

target_group_arn = sys_info[0].strip()
main_url = sys_info[1].strip()
elb_arn = sys_info[3].strip()
group_id = sys_info[4].strip()
group_name = sys_info[5].strip()
main_instance_id = sys_info[6].strip()

ec2_resource = boto3.resource('ec2')
ec2_client = boto3.client('ec2')
elb = boto3.client('elbv2')

instance_ids = [main_instance_id]
for id in worker_nodes.values():
    instance_ids.append(id)

# Delete load balancer
elb.delete_load_balancer(LoadBalancerArn=elb_arn)

# Delete target group
elb.delete_target_group(TargetGroupArn=target_group_arn)

# Terminate instances
ec2_resource.instances.filter(InstanceIds=instance_ids).terminate()

waiter = ec2_client.get_waiter('instance_terminated')
waiter.wait(InstanceIds=instance_ids)

# Delete security group
ec2_client.delete_security_group(GroupId=group_id, GroupName = group_name)

# TODO: wipe nodes.txt and scale_info.txt?