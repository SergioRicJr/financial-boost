variable "aws_region" {
  type        = string
  description = "Regiao AWS alvo."
  default     = "us-east-1"
}

variable "environment" {
  type        = string
  description = "Identificador do ambiente (ex.: dev, staging, prod)."
  default     = "dev"
}

variable "instance_type" {
  type        = string
  description = "Tipo da instancia EC2."
  default     = "t3.micro"
}

variable "key_pair_name" {
  type        = string
  description = "Nome do par de chaves existente na AWS."
  default     = "financialboostec2"
}

variable "db_allocated_storage" {
  type        = number
  description = "Armazenamento alocado (GiB) para o RDS."
  default     = 20
}

variable "ec2_private_key_pem" {
  type        = string
  description = "Conteudo PEM da chave privada usada pelo EC2."
  default     = ""
  sensitive   = true
}