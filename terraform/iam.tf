data "aws_iam_policy_document" "Remove_Deployment_ECS_ALB_assume" {
  statement {
    effect = "Allow"
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

data "aws_iam_policy_document" "Remove_Deployment_ECS_ALB_actions" {
  statement {
    effect = "Allow"
    actions = ["elasticloadbalancing:DeleteTargetGroup", "elasticloadbalancing:DeleteListener", "elasticloadbalancing:DescribeListeners"]

    resources = [ "*" ] # here add the only relevant ALB
  }
  statement {
    effect = "Allow"
    actions = ["dynamodb:DeleteItem", "dynamodb:GetItem", "dynamodb:GetRecords"]

    resources = [ "*" ] # here add the only relevant DynamoDB table
  }
  statement {
    effect = "Allow"
    actions = ["ecs:UpdateService", "ecs:DeleteService"]

    resources = [ "*" ] # here add only the relevant ECS cluster
  }
}

resource "aws_iam_policy" "Remove_Deployment_ECS_ALB_policy" {
  name        = "Remove_Deployment_ECS_ALB_policy"
  description = "Remove_Deployment_ECS_ALB role policy"
  policy      = data.aws_iam_policy_document.Remove_Deployment_ECS_ALB_actions.json
  
  tags = {
    Environment = "Dev"
  }
}

resource "aws_iam_role_policy_attachment" "Remove_Deployment_ECS_ALB_attach" {
  role       = aws_iam_role.Remove_Deployment_ECS_ALB.name
  policy_arn = aws_iam_policy.Remove_Deployment_ECS_ALB_policy.arn
}

resource "aws_iam_role" "Remove_Deployment_ECS_ALB" {
  name               = "Remove_Deployment_ECS_ALB_role"
  assume_role_policy = data.aws_iam_policy_document.Remove_Deployment_ECS_ALB_assume.json

  tags = {
    Environment = "Dev"
  }
}