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

output "alb_dns_name" {
  description = "Nombre DNS del ALB para configurar CloudFront como origen"
  value       = aws_lb.frontend.dns_name
}

output "alb_zone_id" {
  description = "Hosted zone ID de AWS del ALB para futuros alias DNS"
  value       = aws_lb.frontend.zone_id
}

output "alb_security_group_id" {
  description = "Security group de entrada del ALB, restringido a CloudFront"
  value       = aws_security_group.alb.id
}

output "frontend_security_group_id" {
  description = "Security group de tareas frontend, acepta tráfico solo del ALB"
  value       = aws_security_group.frontend.id
}

output "frontend_ecr_repository_url" {
  description = "URL del repositorio ECR para publicar la imagen frontend"
  value       = aws_ecr_repository.frontend.repository_url
}

output "frontend_ecs_cluster_name" {
  description = "Nombre del cluster ECS que ejecuta el frontend"
  value       = aws_ecs_cluster.frontend.name
}

output "frontend_ecs_service_name" {
  description = "Nombre del servicio ECS frontend"
  value       = aws_ecs_service.frontend.name
}

output "route53_zone_id" {
  description = "ID de la zona alojada; se crea únicamente en prod"
  value       = try(aws_route53_zone.primary[0].zone_id, null)
}

output "route53_name_servers" {
  description = "Name servers que deben configurarse en el registrador del dominio"
  value       = try(aws_route53_zone.primary[0].name_servers, [])
}