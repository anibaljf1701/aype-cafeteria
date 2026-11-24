output "menu_table_name" {
  description = "DynamoDB menu table name"
  value       = aws_dynamodb_table.menu.name
}

output "menu_table_arn" {
  description = "DynamoDB menu table ARN"
  value       = aws_dynamodb_table.menu.arn
}

output "reservas_table_name" {
  description = "DynamoDB reservations table name"
  value       = aws_dynamodb_table.reservas.name
}

output "reservas_table_arn" {
  description = "DynamoDB reservations table ARN"
  value       = aws_dynamodb_table.reservas.arn
}

output "ssm_parameter_paths" {
  description = "SSM parameter paths consumed by the SAM stack"
  value = {
    menu_name     = aws_ssm_parameter.menu_table_name.name
    menu_arn      = aws_ssm_parameter.menu_table_arn.name
    reservas_name = aws_ssm_parameter.reservas_table_name.name
    reservas_arn  = aws_ssm_parameter.reservas_table_arn.name
  }
}