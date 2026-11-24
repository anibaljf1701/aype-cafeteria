terraform {
  required_version = ">= 1.5.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  backend "s3" {}
}

provider "aws" {
  region = var.aws_region
}

locals {
  tags = {
    Environment = var.environment
    Project     = var.project_name
    ManagedBy   = "Terraform"
    Layer       = "02-Data"
  }
}

resource "aws_dynamodb_table" "menu" {
  name                        = "${var.project_name}-${var.environment}-menu"
  billing_mode                = "PAY_PER_REQUEST"
  hash_key                    = "id"
  deletion_protection_enabled = var.environment == "prod"

  attribute {
    name = "id"
    type = "S"
  }

  point_in_time_recovery {
    enabled = var.environment == "prod"
  }

  server_side_encryption {
    enabled = true
  }

  tags = local.tags
}

resource "aws_dynamodb_table" "reservas" {
  name                        = "${var.project_name}-${var.environment}-reservas"
  billing_mode                = "PAY_PER_REQUEST"
  hash_key                    = "id"
  deletion_protection_enabled = var.environment == "prod"

  attribute {
    name = "id"
    type = "S"
  }

  point_in_time_recovery {
    enabled = var.environment == "prod"
  }

  server_side_encryption {
    enabled = true
  }

  tags = local.tags
}

resource "aws_ssm_parameter" "menu_table_name" {
  name        = "/${var.project_name}/${var.environment}/dynamodb/menu/name"
  description = "DynamoDB menu table name for ${var.environment}"
  type        = "String"
  value       = aws_dynamodb_table.menu.name
  tags        = local.tags
}

resource "aws_ssm_parameter" "menu_table_arn" {
  name        = "/${var.project_name}/${var.environment}/dynamodb/menu/arn"
  description = "DynamoDB menu table ARN for ${var.environment}"
  type        = "String"
  value       = aws_dynamodb_table.menu.arn
  tags        = local.tags
}

resource "aws_ssm_parameter" "reservas_table_name" {
  name        = "/${var.project_name}/${var.environment}/dynamodb/reservas/name"
  description = "DynamoDB reservations table name for ${var.environment}"
  type        = "String"
  value       = aws_dynamodb_table.reservas.name
  tags        = local.tags
}

resource "aws_ssm_parameter" "reservas_table_arn" {
  name        = "/${var.project_name}/${var.environment}/dynamodb/reservas/arn"
  description = "DynamoDB reservations table ARN for ${var.environment}"
  type        = "String"
  value       = aws_dynamodb_table.reservas.arn
  tags        = local.tags
}