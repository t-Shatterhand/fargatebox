import json
import boto3


def lambda_handler(event, context):
    headers = event.get("headers")
    api_key = headers.get("x-api-key")

    cluster_arn = "arn:aws:ecs:eu-north-1:123456789012:cluster/Diploma_cluster"

    dynamodb = boto3.client('dynamodb')
    ecs = boto3.client('ecs')
    elb = boto3.client('elbv2')

    dynamodb_record = dynamodb.get_item(
        Key={'api_key': {'S': api_key}},
        TableName='Diploma_User_Table',
    )

    answer = {}

    if 'Item' not in dynamodb_record:
        answer['response'] = "You have no images deployed currently"
        return {
            'statusCode': 400,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps(answer)
        }

    service_id = dynamodb_record['Item'].get('service_id', {}).get('S', "")

    if service_id == "":
        answer['response'] = "Your deployment is not fully ready yet. Try again later"
        return {
            'statusCode': 400,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps(answer)
        }

    listener_arn = dynamodb_record['Item']['listener_arn']['S']
    target_group_arn = dynamodb_record['Item']['target_group_arn']['S']
    port = dynamodb_record['Item']['port']['N']

    is_service_removed = True
    is_alb_removed = True

    update_service_response = ecs.update_service(
        cluster=cluster_arn,
        service=service_id,
        desiredCount=0
    )

    try:
        listener_delete_response = elb.delete_listener(ListenerArn=listener_arn)
        is_alb_removed = True
    except:
        is_alb_removed = False

    try:
        target_group_delete_response = elb.delete_target_group(TargetGroupArn=target_group_arn)
        is_alb_tg_removed = True
    except:
        is_alb_tg_removed = False

    try:
        service_delete_response = ecs.delete_service(
            cluster=cluster_arn,
            service=service_id,
            force=True
        )
        is_service_removed = True
    except:
        is_service_removed = False

    try:
        record_delete_response = dynamodb.delete_item(
            TableName='Diploma_User_Table',
            Key={'api_key': {'S': api_key}}
        )
        is_db_record_removed = True
    except:
        is_db_record_removed = False

    if not is_service_removed:
        answer['ecs'] = 'There was a problem removing ECS service'
    if not is_alb_removed:
        answer['alb'] = 'There was a problem removing Load balancer listener'
    if not is_alb_tg_removed:
        answer['tg'] = 'There was a problem removing Load balancer target group'
    if not is_db_record_removed:
        answer['db'] = 'There was a problem removing a database record'

    answer['response'] = 'Removed current image deployment'

    return {
        'statusCode': 200,
        'headers': {'Content-Type': 'application/json'},
        'body': json.dumps(answer)
    }