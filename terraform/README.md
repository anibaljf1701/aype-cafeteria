# Terraform

La infraestructura se organiza por capas y entornos. La capa `01-network` crea
una VPC con dos subredes públicas en distintas zonas de disponibilidad, un
Internet Gateway y rutas públicas. No crea NAT Gateways, subredes privadas,
security groups ni servicios de aplicación.

## Requisitos

- Terraform 1.5 o posterior.
- Credenciales de AWS con permisos para administrar VPC y acceso al backend.
- El bucket S3 `aype-tfstate-portfolio` y la tabla DynamoDB `terraform-locks`
  deben existir antes de inicializar Terraform.

## Red

Desde `terraform/layers/01-network`, inicializa y planifica cada entorno con su
configuración correspondiente:

```bash
terraform init -reconfigure -backend-config=environments/dev.backend.hcl
terraform plan -var-file=environments/dev.tfvars
```

Para producción, usa `prod` en ambos archivos:

```bash
terraform init -reconfigure -backend-config=environments/prod.backend.hcl
terraform plan -var-file=environments/prod.tfvars
```

Cada entorno tiene su propio estado S3. La clave de estado de `prod` conserva la
ruta previamente configurada (`layers/01-network/terraform.tfstate`); `dev` usa
`layers/dev/01-network/terraform.tfstate`.

Los servicios posteriores podrán desplegar el ALB y Fargate en las subredes
públicas. El servicio ECS deberá asignar IP pública a sus tareas y restringir su
security group para aceptar tráfico únicamente desde el security group del ALB.
La restricción de entrada del ALB a CloudFront se definirá junto con ese ALB.

La zona alojada de Route 53 queda pendiente de conocer el dominio que se
registrará. Cuando se defina, se añadirá su recurso Terraform y la delegación DNS
correspondiente.