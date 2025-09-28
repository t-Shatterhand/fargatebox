# Package the Lambda function code
data "archive_file" "Remove_Deployment_ECS_ALB_zip" {
  type        = "zip"
  source_file = "../lambda_code/Remove_Deployment_ECS_ALB.py"
  output_path = "../lambda_code/Remove_Deployment_ECS_ALB_${replace(replace(timestamp(), ":", ""), "-", "")}.zip"

  depends_on = [ local_file.Remove_Deployment_ECS_ALB_py ]
}

# Lambda function
resource "aws_lambda_function" "Remove_Deployment_ECS_ALB" {
  filename         = data.archive_file.Remove_Deployment_ECS_ALB_zip.output_path
  function_name    = "Remove_Deployment_ECS_ALB"
  role             = aws_iam_role.Remove_Deployment_ECS_ALB.arn
  handler          = "lambda_function.lambda_handler"
  source_code_hash = data.archive_file.Remove_Deployment_ECS_ALB_zip.output_base64sha256

  runtime = "python3.12"

  tags = {
    Environment = "Dev"
  }
}