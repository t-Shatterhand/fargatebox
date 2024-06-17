import json
import boto3
import secrets
import random


def lambda_handler(event, context):
    ecs = boto3.client('ecs')
    elb = boto3.client('elbv2')
    dynamodb = boto3.client('dynamodb')

    unique_id = secrets.token_hex(32)
    service_id = event['api_key'] + unique_id

    cluster_arn = 'arn:aws:ecs:eu-north-1:123456789012:cluster/Diploma_cluster'
    elb_arn = 'arn:aws:elasticloadbalancing:eu-north-1:123456789012:loadbalancer/app/albtest/5fddcaec18b63796'
    certificate_arn = 'arn:aws:acm:eu-north-1:123456789012:certificate/eee555444-149c-47c1-8af8-931c34072218'

    scan = dynamodb.scan(TableName='Diploma_User_Table')
    busy_ports = [int(x.get("port", {}).get("N", "0")) for x in scan.get("Items")]
    out_port = random.choice(list(set([x for x in range(9000, 11000)]) - set(busy_ports)))
    event['out_port'] = out_port

    environment_vars = []
    for key, value in event['variables'].items():
        environment_vars.append(
            {
                "name": key,
                "value": value
            }
        )

    listener_arn = ""
    target_group_arn = ""
    service_arn = ""
    event['is_failed'] = False
    listener_removed = False
    tg_removed = False
    service_removed = False
    db_record_removed = False

    try:
        register_task_definition_response = ecs.register_task_definition(

            family=event['api_key'],
            networkMode='awsvpc',
            requiresCompatibilities=['FARGATE'],
            cpu='512',
            memory='1024',
            runtimePlatform={'operatingSystemFamily': 'LINUX'},
            containerDefinitions=[
                {
                    'name': 'container-' + event['api_key'],
                    'image': event['image'],
                    'portMappings': [
                        {
                            'containerPort': event['in_port'],
                            'hostPort': event['in_port'],
                            'protocol': 'tcp',
                        }
                    ],
                    'essential': True,
                    'environment': environment_vars,
                    'cpu': 512,
                    'memory': 1024,
                }]

        )

        create_target_group_response = elb.create_target_group(
            Name='tg-' + str(out_port),
            Protocol='HTTP',
            Port=event['in_port'],
            VpcId='vpc-0d34b702b2b8018f8',
            HealthCheckEnabled=True,
            HealthCheckIntervalSeconds=40,
            HealthCheckTimeoutSeconds=15,
            HealthyThresholdCount=5,
            UnhealthyThresholdCount=8,
            TargetType='ip',
        )

        target_group_arn = create_target_group_response.get('TargetGroups', [{}])[0].get('TargetGroupArn', "")

        create_listener_response = elb.create_listener(
            LoadBalancerArn=elb_arn,
            Protocol='HTTPS',
            Port=out_port,
            DefaultActions=[
                {
                    'Type': 'forward',
                    'TargetGroupArn': target_group_arn,
                }
            ],
            Certificates=[
                {
                    'CertificateArn': certificate_arn
                },
            ]
        )

        listener_arn = create_listener_response.get('Listeners', [{}])[0].get('ListenerArn', "")

        create_service_response = ecs.create_service(
            cluster=cluster_arn,
            serviceName=service_id,
            taskDefinition=event['api_key'],
            loadBalancers=[
                {
                    'targetGroupArn': target_group_arn,
                    'containerName': 'container-' + event['api_key'],
                    'containerPort': event['in_port']
                },
            ],
            desiredCount=1,
            launchType='FARGATE',
            deploymentConfiguration={
                'deploymentCircuitBreaker': {
                    'enable': True,
                    'rollback': True
                },
                'maximumPercent': 200,
                'minimumHealthyPercent': 100
            },
            networkConfiguration={
                'awsvpcConfiguration': {
                    'subnets': [
                        'subnet-05f8d1a702539c162', 'subnet-02c1dda1e78052c0c', 'subnet-0d44f6738bd6954b8'
                    ],
                    'assignPublicIp': 'ENABLED'
                }
            },
            healthCheckGracePeriodSeconds=60,
            schedulingStrategy='REPLICA',
            deploymentController={
                'type': 'ECS'
            }
        )
        service_arn = create_service_response.get('service', {}).get('serviceArn', "")

    except:
        event['is_failed'] = True

    if (target_group_arn == "") or (listener_arn == "") or (service_arn == ""):
        # Something failed to create
        event['is_failed'] = True

    if event['is_failed']:
        # Remove everything created yet
        if listener_arn != "":
            try:
                listener_delete_response = elb.delete_listener(ListenerArn=listener_arn)
                listener_removed = True
            except:
                listener_removed = False
        if target_group_arn != "":
            try:
                target_group_delete_response = elb.delete_target_group(TargetGroupArn=target_group_arn)
                tg_removed = True
            except:
                tg_removed = False
        if service_arn != "":
            try:
                service_delete_response = ecs.delete_service(
                    cluster=cluster_arn,
                    service=service_id,
                    force=True
                )
                service_removed = True
            except:
                service_removed = False
        try:
            record_delete_response = dynamodb.delete_item(
                TableName='Diploma_User_Table',
                Key={'api_key': {'S': event['api_key']}}
            )
            db_record_removed = True
        except:
            db_record_removed = False

        event['listener_removed'] = listener_removed
        event['tg_removed'] = tg_removed
        event['service_removed'] = service_removed
        event['db_record_removed'] = db_record_removed
        # Exit the execution; Further steps won't start
        return event

    record_update_response = dynamodb.update_item(
        TableName='Diploma_User_Table',
        Key={'api_key': {'S': event['api_key']}},
        ExpressionAttributeNames={
            '#P': 'port',
            '#LA': 'listener_arn',
            '#TA': 'target_group_arn',
            '#SI': 'service_id',
        },
        ExpressionAttributeValues={
            ':p': {'N': str(out_port)},
            ':la': {'S': listener_arn},
            ':ta': {'S': target_group_arn},
            ':si': {'S': service_id}
        },
        UpdateExpression='SET #P = :p, #LA = :la, #TA = :ta, #SI = :si'
    )

    event['service_id'] = service_id

    return event
