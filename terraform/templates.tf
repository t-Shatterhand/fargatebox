resource "local_file" "Remove_Deployment_ECS_ALB_py" {
  filename = "../lambda_code/Remove_Deployment_ECS_ALB.py"
  content = templatefile("../lambda_code/Remove_Deployment_ECS_ALB.py.tftpl", {
    cluster_arn = "test_cluster_arn",
    dynamodb_table_name = "test_table_name"
  })
}

resource "local_file" "Delete_Request_Handler_py" {
  filename = "../lambda_code/Delete_Request_Handler.py"
  content = templatefile("../lambda_code/Delete_Request_Handler.py.tftpl", {
    cluster_arn = "test_cluster_arn",
    dynamodb_table_name = "test_table_name"
  })
}

resource "local_file" "Create_Deployment_ECS_ELB_py" {
  filename = "../lambda_code/Create_Deployment_ECS_ELB.py"
  content = templatefile("../lambda_code/Create_Deployment_ECS_ELB.py.tftpl", {
    cluster_arn = "test_cluster_arn",
    elb_arn = "test_elb_arn", 
    certificate_arn = "test_cert_arn",
    dynamodb_table_name = "test_table_name",
    vpc_id = "test_vpc_id", 
    subnet_ids = "test_subnets"
  })
}
