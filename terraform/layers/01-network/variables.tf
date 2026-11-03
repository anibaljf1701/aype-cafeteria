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
  description = "Entorno de despliegue (dev o prod)"
  type        = string

  validation {
    condition     = contains(["dev", "prod"], var.environment)
    error_message = "El entorno debe ser dev o prod."
  }
}

variable "vpc_cidr" {
  description = "Bloque CIDR de la VPC"
  type        = string
}

variable "public_subnets_cidr" {
  description = "Bloques CIDR para las 2 subredes públicas"
  type        = list(string)
}