terraform {
  required_version = ">= 1.5.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  # Configuración del Backend Remoto (S3 + DynamoDB Lock)
  backend "s3" {
    bucket         = "aype-tfstate-portfolio"
    key            = "layers/01-network/terraform.tfstate"
    region         = "us-east-1"
    dynamodb_table = "terraform-locks"
    encrypt        = true
  }
}

provider "aws" {
  region = var.aws_region
}

# Obtiene dinámicamente las primeras 2 Zonas de Disponibilidad
data "aws_availability_zones" "available" {
  state = "available"
}

module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "~> 5.0"

  name = "${var.project_name}-${var.environment}-vpc"
  cidr = var.vpc_cidr

  # Tomamos 2 AZs automáticamente de la región seleccionada
  azs            = slice(data.aws_availability_zones.available.names, 0, 2)
  public_subnets = var.public_subnets_cidr

  # Decisión de Arquitectura: Cost-Optimized ($0 NAT Gateway)
  enable_nat_gateway = false
  enable_vpn_gateway = false

  # Requerido para resoluciones DNS internas y asignación de IPs en ECS/ALB
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Environment = var.environment
    Project     = var.project_name
    ManagedBy   = "Terraform"
    Layer       = "01-Network"
  }
}