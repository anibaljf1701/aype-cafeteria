# Terraform data layer

This layer owns the persistent DynamoDB tables and publishes each table name
and ARN in SSM Parameter Store. The `menu` table stores menu items; `reservas`
stores cup reservations, daily counters, and tasting reservations.

Tables use on-demand billing and server-side encryption. Production enables
point-in-time recovery and deletion protection. Development tables can be
recreated through Terraform.

The layer has a separate remote state from networking and SAM. Apply it before
deploying the backend so the SSM parameters exist:

```bash
terraform init -reconfigure -backend-config=environments/dev.backend.hcl
terraform plan -var-file=environments/dev.tfvars
terraform apply -var-file=environments/dev.tfvars
```

Use the corresponding `prod` files for production. The state bucket and
`terraform-locks` table must already exist, as documented in the Terraform
README. Do not manage these tables in the SAM stack.