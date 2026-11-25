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

variable "domain_name" {
  description = "Dominio raíz para la zona alojada de Route 53"
  type        = string
  default     = "aype.com"
}

variable "frontend_port" {
  description = "Puerto HTTP del contenedor frontend"
  type        = number
  default     = 80
}

variable "frontend_image_tag" {
  description = "Etiqueta de la imagen frontend publicada en ECR"
  type        = string
  default     = "latest"
}

variable "frontend_desired_count" {
  description = "Cantidad de tareas frontend que ECS debe mantener"
  type        = number
  default     = 1
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