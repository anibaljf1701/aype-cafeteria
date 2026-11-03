output "vpc_id" {
  description = "ID de la VPC creada"
  value       = module.vpc.vpc_id
}

output "public_subnets" {
  description = "Lista de IDs de subredes públicas para ALB y ECS"
  value       = module.vpc.public_subnets
}

output "azs" {
  description = "Zonas de disponibilidad utilizadas (2 AZs)"
  value       = module.vpc.azs
}

output "internet_gateway_id" {
  description = "ID del Internet Gateway asociado a las subredes públicas"
  value       = module.vpc.igw_id
}