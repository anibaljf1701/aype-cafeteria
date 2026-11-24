# AyPe Cafeteria

Aplicación full-stack independiente para la cafetería AyPe. El repositorio reúne el frontend y la API; la infraestructura de AWS se añadirá y documentará aquí como parte del ciclo de vida de la aplicación, reutilizando como referencia los templates del portfolio cuando corresponda.

## Componentes

- `frontend/`: sitio web estático servido por Nginx en contenedor.
- `backend/`: API FastAPI para menú y reservas, con adaptador Mangum para AWS Lambda y DynamoDB.

## Desarrollo local

### Frontend

Construye y ejecuta el contenedor desde la raíz de este repositorio:

```bash
docker build -t aype-frontend:local -f frontend/Dockerfile frontend
docker run --rm -p 8080:80 \
	-e AYPE_API_BASE_URL=http://127.0.0.1:8000 \
	aype-frontend:local
```

Abre `http://localhost:8080`.

### Backend

Consulta [backend/README.md](backend/README.md) para dependencias, configuración de AWS y ejecución local. FastAPI publica la documentación OpenAPI interactiva en `/docs`.

## Infraestructura y despliegue

Terraform administra la infraestructura de red y frontend, junto con los datos
persistentemente almacenados en la capa `terraform/layers/02-data`. AWS SAM
administra la Lambda y API Gateway HTTP; consume desde SSM los nombres y ARNs de
las tablas creadas por Terraform. Consulta [terraform/README.md](terraform/README.md)
y [backend/README.md](backend/README.md) para el orden de despliegue por entorno.

`ecs-fargate-frontend-migration` y `aws-terraform-3tier-architecture` son
proyectos de referencia independientes, no dependencias locales de esta
aplicación.
