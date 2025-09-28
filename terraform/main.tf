/*resource "local_file" "generated_config" {
  filename = "../step_functions/step_function_definition.json"
  content = templatefile("../step_functions/step_function_definition.json.tftpl", {
    create_task_definition_function_arn = "TEST1",
    remove_service_function_arn = "TEST2",
  })
}*/