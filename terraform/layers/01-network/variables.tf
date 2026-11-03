variable "aws_region" {
  description = "Región principal de AWS"
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Nombre del proyecto principal"
  type        = string
  default     = "aype"
}

variable "environment" {
  description = "Entorno de despliegue (prod, dev, staging)"
  type        = string
  default     = "prod"
}

variable "vpc_cidr" {
  description = "Bloque CIDR de la VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "public_subnets_cidr" {
  description = "Bloques CIDR para las 2 subredes públicas"
  type        = list(string)
  default     = ["10.0.1.0/24", "10.0.2.0/24"]
}