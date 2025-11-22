terraform {
  required_version = ">= 1.6.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.50"
    }

    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }

    tls = {
      source  = "hashicorp/tls"
      version = "~> 4.0"
    }
  }
}



locals {
  project_name = "financial boost"
  project_slug = replace(local.project_name, " ", "-")

  tags = {
    Project     = local.project_name
    Environment = var.environment
  }

  az_public  = "${var.aws_region}a"
  az_private = "${var.aws_region}b"
  private_key_pem = var.ec2_private_key_pem != "" ? trimspace(var.ec2_private_key_pem) : file("${path.module}/financialboostec2.pem")
}

data "aws_ssm_parameter" "al2023_ami" {
  name = "/aws/service/ami-amazon-linux-latest/al2023-ami-kernel-6.1-x86_64"
}

data "tls_public_key" "financial_boost" {
  private_key_pem = local.private_key_pem
}

# ------------------------------
# Rede
# ------------------------------

resource "aws_vpc" "financial_boost" {
  cidr_block           = "10.0.0.0/23"
  enable_dns_support   = true
  enable_dns_hostnames = true

  tags = merge(local.tags, {
    Name = "financial boost vpc"
  })
}

resource "aws_internet_gateway" "financial_boost" {
  vpc_id = aws_vpc.financial_boost.id

  tags = merge(local.tags, {
    Name = "financial boost gateway"
  })
}

resource "aws_subnet" "public" {
  vpc_id                  = aws_vpc.financial_boost.id
  cidr_block              = "10.0.1.0/24"
  availability_zone       = local.az_public
  map_public_ip_on_launch = true

  tags = merge(local.tags, {
    Name = "financial boost rede publica"
  })
}

resource "aws_subnet" "private" {
  vpc_id                  = aws_vpc.financial_boost.id
  cidr_block              = "10.0.0.0/24"
  availability_zone       = local.az_private
  map_public_ip_on_launch = false

  tags = merge(local.tags, {
    Name = "financial boost rede privada"
  })
}

resource "aws_route_table" "public" {
  vpc_id = aws_vpc.financial_boost.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.financial_boost.id
  }

  tags = merge(local.tags, {
    Name = "financial boost public rt"
  })
}

resource "aws_route_table_association" "public_subnet" {
  subnet_id      = aws_subnet.public.id
  route_table_id = aws_route_table.public.id
}

# ------------------------------
# S3
# ------------------------------

resource "aws_s3_bucket" "images" {
  bucket        = "financial-boost-imagens"
  force_destroy = false

  tags = merge(local.tags, {
    Name = "financial boost imagens"
  })
}

resource "aws_s3_bucket_ownership_controls" "images" {
  bucket = aws_s3_bucket.images.id

  rule {
    object_ownership = "BucketOwnerEnforced"
  }
}

resource "aws_s3_bucket_public_access_block" "images" {
  bucket = aws_s3_bucket.images.id

  block_public_acls       = false
  ignore_public_acls      = false
  block_public_policy     = false
  restrict_public_buckets = false
}

resource "aws_s3_bucket_policy" "images_public_read" {
  bucket = aws_s3_bucket.images.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid       = "PublicReadGetObject"
        Effect    = "Allow"
        Principal = "*"
        Action    = ["s3:GetObject"]
        Resource = [
          aws_s3_bucket.images.arn,
          "${aws_s3_bucket.images.arn}/*"
        ]
      }
    ]
  })

  depends_on = [
    aws_s3_bucket_public_access_block.images,
    aws_s3_bucket_ownership_controls.images
  ]
}

# ------------------------------
# IAM
# ------------------------------

data "aws_iam_policy_document" "ec2_assume_role" {
  statement {
    effect = "Allow"

    principals {
      type        = "Service"
      identifiers = ["ec2.amazonaws.com"]
    }

    actions = ["sts:AssumeRole"]
  }
}

resource "aws_iam_role" "ec2_s3_full_access" {
  name               = "ec2-s3-full-access"
  assume_role_policy = data.aws_iam_policy_document.ec2_assume_role.json

  tags = merge(local.tags, {
    Name = "ec2 S3 full access"
  })
}

resource "aws_iam_role_policy_attachment" "ec2_s3_full_access" {
  role       = aws_iam_role.ec2_s3_full_access.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonS3FullAccess"
}

resource "aws_iam_instance_profile" "ec2_s3_full_access" {
  name = "ec2-s3-full-access"
  role = aws_iam_role.ec2_s3_full_access.name
}

# ------------------------------
# Seguranca
# ------------------------------

resource "aws_security_group" "ec2" {
  name        = "financial-boost-ec2-sg"
  description = "Libera SSH/HTTP/HTTPS/8080"
  vpc_id      = aws_vpc.financial_boost.id

  ingress {
    description = "SSH"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "HTTP"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "HTTPS"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "Aplicacao Spring Boot"
    from_port   = 8080
    to_port     = 8080
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(local.tags, {
    Name = "financial boost ec2 security group"
  })
}

resource "aws_security_group" "rds" {
  name        = "financial-boost-rds-sg"
  description = "Permite PostgreSQL apenas a partir do SG do EC2"
  vpc_id      = aws_vpc.financial_boost.id

  ingress {
    description      = "PostgreSQL"
    from_port        = 5432
    to_port          = 5432
    protocol         = "tcp"
    security_groups  = [aws_security_group.ec2.id]
    ipv6_cidr_blocks = []
    cidr_blocks      = []
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(local.tags, {
    Name = "financial boost rds security group"
  })
}

# ------------------------------
# Chaves e EC2
# ------------------------------

resource "aws_key_pair" "financial_boost" {
  key_name   = var.key_pair_name
  public_key = data.tls_public_key.financial_boost.public_key_openssh

  tags = merge(local.tags, {
    Name = "financial boost key pair"
  })
}

resource "aws_instance" "java_service" {
  ami                         = data.aws_ssm_parameter.al2023_ami.value
  instance_type               = var.instance_type
  subnet_id                   = aws_subnet.public.id
  associate_public_ip_address = true
  availability_zone           = local.az_public
  key_name                    = aws_key_pair.financial_boost.key_name
  iam_instance_profile        = aws_iam_instance_profile.ec2_s3_full_access.name
  vpc_security_group_ids      = [aws_security_group.ec2.id]

  user_data = <<-EOF
              #!/bin/bash
              sudo yum update -y
              sudo yum install -y java-21-amazon-corretto-headless
              EOF

  tags = merge(local.tags, {
    Name = "Java Service financial boost"
  })
}

# ------------------------------
# RDS
# ------------------------------

resource "aws_db_subnet_group" "financial_boost" {
  name       = "financial-boost-db-subnets"
  subnet_ids = [aws_subnet.private.id, aws_subnet.public.id]

  tags = merge(local.tags, {
    Name = "financial boost db subnet group"
  })
}

resource "aws_db_instance" "financial_boost" {
  identifier                 = "financial-boost-db"
  db_name                    = "financialboost"
  engine                     = "postgres"
  engine_version             = "15.7"
  instance_class             = "db.t4g.micro"
  allocated_storage          = var.db_allocated_storage
  storage_type               = "gp3"
  username                   = "postgres"
  manage_master_user_password = true
  db_subnet_group_name       = aws_db_subnet_group.financial_boost.name
  availability_zone          = local.az_private
  vpc_security_group_ids     = [aws_security_group.rds.id]
  backup_retention_period    = 1
  deletion_protection        = false
  skip_final_snapshot        = true
  copy_tags_to_snapshot      = true
  auto_minor_version_upgrade = true
  publicly_accessible        = false
  storage_encrypted          = true

  tags = merge(local.tags, {
    Name = "financial boost Database"
  })
}

# ------------------------------
# Outputs
# ------------------------------

output "ec2_public_ip" {
  description = "Endereco publico da instancia Spring Boot."
  value       = aws_instance.java_service.public_ip
}

output "s3_bucket_name" {
  description = "Bucket de imagens."
  value       = aws_s3_bucket.images.bucket
}

output "rds_endpoint" {
  description = "Endpoint de conexao do PostgreSQL."
  value       = aws_db_instance.financial_boost.endpoint
}
