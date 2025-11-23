# FinancialBoost API

API financeira em Spring Boot responsável por autenticação JWT, categorias e transações com upload para S3. A infraestrutura roda em AWS (VPC, EC2, RDS, S3, IAM) com provisionamento automática via Terraform e deploy contínuo pelo GitHub Actions.

---

## Sumário

1. [Visão Geral](#visão-geral)
2. [Stack & Arquitetura](#stack--arquitetura)
3. [Domínios e Contratos](#domínios-e-contratos)
4. [Estrutura do Repositório](#estrutura-do-repositório)
5. [Configuração & Variáveis](#configuração--variáveis)
6. [Execução Local](#execução-local)
7. [Testes & Coleção Postman](#testes--coleção-postman)
8. [Infra & Deploy](#infra--deploy)
9. [Observabilidade & Próximos Passos](#observabilidade--próximos-passos)
10. [Referências Rápidas](#referências-rápidas)

---

## Visão Geral

- API REST com autenticação JWT, CRUD de categorias e transações com filtros e paginação.
- PostgreSQL 15 + Flyway para migrações.
- Upload de comprovantes para S3 público com política de leitura.
- Pipelines GitHub Actions: provisionamento Terraform + deploy contínuo para EC2.
- Infra segura: VPC isolada, RDS privado, EC2 público com role de acesso ao S3.

---

## Stack & Arquitetura

| Camada | Tecnologias |
| --- | --- |
| Aplicação | Spring Boot 3.5, Spring Web, Spring Data JPA, Spring Security, JWT (Auth0), Flyway, AWS SDK S3, Lombok |
| Banco | PostgreSQL (local/RDS), H2 para testes |
| Infra | AWS (VPC, Subnets, IGW, SG, EC2 t3.micro, RDS db.t4g.micro, S3, IAM) |
| IaC | Terraform ≥ 1.8.3 com backend remoto (S3 + DynamoDB) e workspaces |
| Entrega | GitHub Actions + OIDC assumindo a role `github-actions-sergioRicJr-pipeline` |
| Container | Dockerfile multi-stage + Docker Compose |

---

## Domínios e Contratos

| Domínio | Rotas principais | Observações |
| --- | --- | --- |
| Auth | `POST /auth/register` / `POST /auth/login` | BCrypt + JWT (2h). |
| Categorias | CRUD completo | Sempre filtrado pelo usuário autenticado. |
| Transações | CRUD + filtros + upload | Recebe `MultipartFile image`; envia ao S3. Filtros por tipo, operação, valor e data. |
| Balances | Entidade pronta | Controller/Service planejados. |

- DTOs aceitam `operation` (`POSITIVE`, `NEGATIVE`) e `type` (`PIX`, `TED`, `DOC`, `TEF`, `BOLETO`).
- `TransactionResponseDTO` retorna `imgUrl` do S3; `CategoryResponseDTO` inclui `userId`.
- Exemplos completos na collection `postman/financialboost.postman_collection.json`.

---

## Estrutura do Repositório

```
├── Dockerfile
├── docker-compose.yaml
├── infra/
│   ├── backend.tf              # Backend remoto (S3)
│   ├── main.tf                 # Todos os recursos AWS
│   ├── provider.tf             # Seleção de região
│   ├── variables.tf            # Variáveis globais
│   └── envs/
│       ├── dev/terraform.tfvars
│       └── prod/...
├── postman/financialboost.postman_collection.json
├── src/
│   ├── main/java/com/financialboost/api
│   │   ├── controllers/ (auth/category/transaction)
│   │   ├── domain/ (user/category/transaction/balance)
│   │   ├── infra/security & config
│   │   ├── repository/
│   │   └── services/ (AuthorizationService/FileService)
│   └── main/resources/
│       ├── application.properties
│       └── db/migration/*.sql
└── .github/workflows/
    ├── terraform.yaml
    ├── terraform-develop.yaml
    └── deploy-develop.yaml
```

---

## Configuração & Variáveis

### Pré-requisitos
- Git, JDK 17+ (21 recomendado), Maven 3.9+ (ou `./mvnw`), Docker 24+ / Compose v2, AWS CLI v2, Terraform ≥ 1.8.3, Postman/Newman.

| Variável | Descrição | Default |
| --- | --- | --- |
| `DB_URL` | JDBC da base (`jdbc:postgresql://host:porta/banco`) | `jdbc:postgresql://localhost:5435/financialboost` |
| `DB_USER` / `DB_PASSWORD` | Credenciais da base | `root` / `root` |
| `JWT_SECRET` | Chave HMAC usada no JWT | `123456789` (use um valor forte em produção) |
| `AWS_REGION` | Região usada pelo `AWSConfig` | `us-east-1` |
| `AWS_BUCKET_NAME` | Bucket para `FileService` | `financialboostimg` |
| `LOG_LEVEL` | Nível de log Spring (`DEBUG`, `INFO`) | `DEBUG` |

### Docker Compose (`docker-compose.yaml`)

- Serviço `app` exporta `DB_URL`, `DB_USER`, `DB_PASSWORD`; adicione `JWT_SECRET`, `AWS_REGION`, `AWS_BUCKET_NAME` via `--env-file` ou editando o compose.
- Serviço `postgres` sobe `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`.

### Segredos do GitHub Actions

| Segredo | Uso |
| --- | --- |
| `C2_KEY_PEM` | PEM do par de chaves `financialboostec2` (Terraform e SSH). |
| `DB_URL`, `DB_USER`, `DB_PASSWORD` | Montam `app.env` entregue ao EC2. |
| `S3_BUCKET` | Nome do bucket usado pela aplicação no EC2. |
| `JWT_SECRET` | Mesmo valor usado em produção. |
| `EC2_HOST`, `EC2_USER` | Destino do deploy (`ec2-user@<ip>`). |

Credenciais AWS para as pipelines são obtidas via OIDC assumindo a role `arn:aws:iam::238309559213:role/github-actions-sergioRicJr-pipeline` (não há `AWS_ACCESS_KEY_ID` hardcoded).

---

## Pré-requisitos e Configuração de CLI

1. **Ferramentas**
   - Git
   - JDK 17 (ou 21 se preferir rodar igual ao EC2)
   - Maven 3.9+ (ou `./mvnw`)
   - Docker 24+ e Docker Compose v2
   - AWS CLI v2
   - Terraform >= 1.8.3
   - Postman ou Newman

2. **AWS CLI**
   ```bash
   aws configure --profile financialboost
   # ou `aws configure sso` se usar AWS SSO
   export AWS_PROFILE=financialboost
   export AWS_REGION=us-east-1
   ```

3. **Credenciais para o `FileService`**
   - O `DefaultAWSCredentialsProviderChain` procura credenciais nesta ordem: variáveis de ambiente → `~/.aws/credentials` → perfil EC2.
   - Para rodar localmente, garanta que `AWS_ACCESS_KEY_ID`/`AWS_SECRET_ACCESS_KEY` estejam disponíveis ou que `AWS_PROFILE` esteja configurado.

4. **Par de chaves EC2**
   - O Terraform espera `financialboostec2.pem` no diretório `infra/` ou o conteúdo via `TF_VAR_ec2_private_key_pem`.
   - Proteja o arquivo: `chmod 600 infra/financialboostec2.pem`.

---

## Execução Local

1. **Clonar e configurar variáveis**
   ```bash
   git clone https://github.com/SergioRicJr/financial-boost
   cd financialboost-api
   ```
   Crie um arquivo `local.env` (usado pelo Compose):
   ```ini
   JWT_SECRET=dev-secret
   AWS_REGION=us-east-1
   AWS_BUCKET_NAME=financialboost-local
   DB_URL=jdbc:postgresql://postgres:5432/financialboost
   DB_USER=root
   DB_PASSWORD=root
   ```

2. **Subir os contêineres**
   ```bash
   docker compose --env-file local.env up --build -d
   docker compose logs -f app
   ```
   - `app` escuta em `localhost:8000` → encaminha para `8080` no contêiner.
   - `postgres` expõe `5435` para acesso externo (por exemplo, pgAdmin).

3. **Verificar migrações**
   - Flyway roda automaticamente ao subir.
   - Conferir tabelas (opcional):
     ```bash
     psql -h localhost -p 5435 -U root -d financialboost -c "\dt"
     ```

4. **Encerrar**
   ```bash
   docker compose down -v
   ```
   (remove contêineres e volume efêmero do Postgres).


---

## Execução Local com Maven

1. **Provisionar um PostgreSQL local**
   ```bash
   docker run --name financialboost-db -e POSTGRES_PASSWORD=root -e POSTGRES_USER=root \
     -e POSTGRES_DB=financialboost -p 5435:5432 -d postgres:15.2
   ```

2. **Exportar variáveis (Linux/macOS)**
   ```bash
   export DB_URL=jdbc:postgresql://localhost:5435/financialboost
   export DB_USER=root
   export DB_PASSWORD=root
   export AWS_REGION=us-east-1
   export AWS_BUCKET_NAME=financialboostimg
   export JWT_SECRET=dev-secret
   ```
   *(No Windows PowerShell use `$env:DB_URL="..."` etc.)*

3. **Build e run**
   ```bash
   ./mvnw clean package
   java -jar target/api-0.0.1-SNAPSHOT.jar
   # ou
   ./mvnw spring-boot:run
   ```

4. **Health-check**
   - A API não expõe `/actuator` por padrão. Use `POST /auth/register` seguido de `POST /auth/login` para validar.

---

## Testes & Coleção Postman

- Caminho: `postman/financialboost.postman_collection.json`.
- Passos:
  1. Importar a collection.
  2. Ajustar `baseUrl` para:
     - `http://localhost:8000` (Docker)
     - `http://localhost:8080` (Maven local)
     - `http://<ec2-public-ip>:8080` (produção/dev cloud)
  3. Executar na ordem sugerida (Auth → Categories → Transactions). Scripts de teste salvam `authToken`, `categoryId`, `transactionId` automaticamente.
  4. Para anexar comprovantes, habilite o campo `image` e aponte para um arquivo real.

- Também é possível rodar via CLI:
  ```bash
  newman run postman/financialboost.postman_collection.json --env-var baseUrl=http://localhost:8000
  ```

---

## Infra & Deploy (Terraform)

### Recursos Principais (`infra/main.tf`)

- **Rede**: `aws_vpc`, subnets pública (`10.0.1.0/24`) e privada (`10.0.0.0/24`), IGW, rota pública.
- **S3**: Bucket `financial-boost-imagens` com política de leitura pública e `BucketOwnerEnforced`.
- **IAM**: Role + Instance Profile com `AmazonS3FullAccess` anexado ao EC2.
- **Segurança**:
  - SG do EC2 liberando SSH(22)/HTTP(80)/HTTPS(443)/API(8080) para `0.0.0.0/0`.
  - SG do RDS permitindo apenas tráfego do SG do EC2 na porta 5432.
- **Compute**: `aws_instance` (AMI Amazon Linux 2023 via SSM, `t3.micro`, user data instala Java 21).
- **Banco**: `aws_db_instance` Postgres 15.7 (`db.t4g.micro`, `gp3`, storage 20 GiB, `manage_master_user_password = true`, não público).
- **Outputs**: `ec2_public_ip`, `s3_bucket_name`, `rds_endpoint`.

### Variáveis e workspaces

- `infra/variables.tf` define `aws_region`, `environment`, `instance_type`, `key_pair_name`, `db_allocated_storage`, `ec2_private_key_pem`.
- `infra/envs/<env>/terraform.tfvars` parametriza cada ambiente (dev/prod).
- Backend remoto (`infra/backend.tf`) depende dos recursos:
  - Bucket: `sergioricjr-us-east-1-terraform-state-file`
  - Dynamo: `sergioricjr-us-east-1-terraform-lock`

### Execução manual

```bash
cd infra
export TF_VAR_ec2_private_key_pem="$(cat financialboostec2.pem)"
terraform init \
  -backend-config="bucket=sergioricjr-us-east-1-terraform-state-file" \
  -backend-config="key=financialboost-api" \
  -backend-config="region=us-east-1" \
  -backend-config="dynamodb_table=sergioricjr-us-east-1-terraform-lock"

terraform workspace select dev || terraform workspace new dev
terraform plan -var-file=envs/dev/terraform.tfvars -out=dev.plan
terraform apply dev.plan
```

> ⚠️ O workflow `terraform.yaml` chama `terraform apply` logo após o plano; não há etapa de aprovação. Rode apenas quando tiver certeza das alterações.

### Ajustes comuns

- **Novo ambiente**: copiar `infra/envs/dev/terraform.tfvars` para `infra/envs/<env>/terraform.tfvars`, criar workspace e atualizar workflows (inputs).
- **Key Pair**: atualize `var.key_pair_name` e mantenha o PEM seguro. Se `TF_VAR_ec2_private_key_pem` estiver vazio, o módulo tenta ler `infra/financialboostec2.pem`.
- **Senha do banco**: como está gerenciada pela AWS Secrets Manager, use o output do RDS para configurar `DB_URL` e consulte o Secrets Manager para obter usuário/senha.

---

## Passo a passo de configuração AWS (Manual)

Mesmo utilizando Terraform, às vezes é necessário subir a infraestrutura na mão (laboratórios, troubleshooting, ambientes pontuais). Abaixo está o roteiro completo usando apenas o Console AWS, seguindo exatamente os mesmos parâmetros já adotados pelo projeto.

### 1. Configuração da VPC (Virtual Private Cloud) e redes

| Serviço/Componente | Ação de Criação e Configuração | Observações e Detalhes | Fonte(s) |
| --- | --- | --- | --- |
| **VPC** | Criar nova VPC. | **Nome:** `financial boost vpc`. **Bloco CIDR IPv4:** `10.0.0.0/23` (512 IPs disponíveis). | Console AWS |
| **Internet Gateway (IGW)** | Criar e associar à VPC. | **Nome:** `financial boost Gateway`. Vincular à `financial boost vpc`. | Console AWS |
| **Subnet Pública** | Criar dentro da VPC. | **Nome:** `financial boost rede pública`. **CIDR:** `10.0.1.0/24`. **AZ:** `us-east-1a`. Hospeda o EC2. | Console AWS |
| **Subnet Privada** | Criar dentro da VPC. | **Nome:** `financial boost rede privada`. **CIDR:** `10.0.0.0/24`. **AZ:** `us-east-1b`. Hospeda o RDS. | Console AWS |
| **Tabela de Rotas** | Atualizar rota da subnet pública. | Adicionar rota `0.0.0.0/0` apontando para o IGW `financial boost Gateway`. | Console AWS |

### 2. Configuração do S3 (Simple Storage Service)

| Serviço/Componente | Ação de Criação e Configuração | Observações e Detalhes | Fonte(s) |
| --- | --- | --- | --- |
| **Bucket S3** | Criar novo bucket. | **Nome:** `financial boost imagens`. Desabilitar ACLs. Desbloquear acesso público para leitura. | Console AWS |
| **Política do Bucket** | Ajustar Permissões → Política do Bucket. | Anexar política *Public read* permitindo `s3:GetObject`. Ajuste o ARN se usar outro nome. | Console AWS |

Política sugerida:

```
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "PublicReadGetObject",
      "Principal": "*",
      "Effect": "Allow",
      "Action": [
        "s3:GetObject"
      ],
      "Resource": "arn:aws:s3:::financial-boost-img/*"
    }
  ]
}
```

### 3. Criação e configuração da instância EC2 (Servidor Java)

| Serviço/Componente | Ação de Criação e Configuração | Observações e Detalhes | Fonte(s) |
| --- | --- | --- | --- |
| **Instância EC2** | Executar instância. | **Nome:** `Java Service financial boost`. **AMI:** Amazon Linux (2023). **Tipo:** `t3.micro`. Criar par de chaves `financialboostec2` (RSA, `.pem`). | Console AWS |
| **Configurações de Rede** | Selecionar rede correta. | **VPC:** `financial boost vpc`. **Subnet:** `financial boost rede pública`. **IP público:** habilitar atribuição automática. | Console AWS |
| **Security Group (EC2)** | Criar SG dedicado. | **Nome:** `financial boost ec2 Security group`. Liberar **SSH (22)**, **HTTP (80)**, **HTTPS (443)** e **TCP 8080** para `0.0.0.0/0`. | Console AWS |
| **User Data** | Automatizar instalação do Java. | Inserir script abaixo ao criar a instância. | Console AWS |

Script:

```bash
#!/bin/bash
sudo yum update -y
sudo yum install -y java-21-amazon-corretto-headless
```

### 4. Criação e configuração do RDS (PostgreSQL)

| Serviço/Componente | Ação de Criação e Configuração | Observações e Detalhes | Fonte(s) |
| --- | --- | --- | --- |
| **Banco de Dados RDS** | Criar banco (modo padrão). | **Motor:** PostgreSQL **15.7-R4**. **Modelo:** Free tier. **Nome:** `financial boost Database`. **Usuário:** `postgres`. Ativar `AWS Secrets Manager` para gerenciar a senha. | Console AWS |
| **Classe da instância** | Selecionar capacidade. | `db.t4g.micro`, armazenamento `gp3` 20 GiB. | Console AWS |
| **Conectividade** | Ajustar acesso. | **VPC:** `financial boost vpc`. **Sub-redes:** use as privadas em múltiplas AZs. **Acesso público:** **Não**. Associar com a instância `Java Service financial boost`. | Console AWS |
| **Security Group (RDS)** | Criar SG específico. | Permitir tráfego **somente** do SG do EC2 na porta 5432. | Console AWS |

### 5. Configuração do IAM (Identity and Access Management)

| Serviço/Componente | Ação de Criação e Configuração | Observações e Detalhes | Fonte(s) |
| --- | --- | --- | --- |
| **IAM Role** | Criar nova Role para EC2. | Entidade confiável: **EC2**. Anexar política `AmazonS3FullAccess`. **Nome:** `ec2 S3 full access`. | Console AWS |
| **Associação ao EC2** | Vincular a Role. | Em `Java Service financial boost` → Ações → Segurança → Modificar função IAM → selecionar `ec2 S3 full access`. | Console AWS |

### 6. Conexão final da aplicação com o RDS

1. Obtenha o **endpoint** do RDS e monte o JDBC: `jdbc:postgresql://<ENDPOINT>/<DATABASE_NAME>`. O banco padrão é `postgres`.
2. No `application.properties`, configure `spring.datasource.url`, `spring.datasource.username=postgres` e `spring.datasource.password` com a senha recuperada no Secrets Manager.
3. Faça o upload do `.jar` (via `scp`) para o EC2, conecte-se por SSH e execute:
   ```bash
   source ~/app.env
   java -jar financial-boost.jar
   ```
4. **RDS**: PostgreSQL 15.7 `db.t4g.micro`, criação padrão, Secrets Manager para a senha, subnets privadas, sem acesso público, SG permitindo 5432 apenas do SG do EC2.
5. **IAM**: role `ec2 S3 full access` (trust EC2 + `AmazonS3FullAccess`) e associação à instância.
6. **Conexão**: resgatar endpoint do RDS (`jdbc:postgresql://<endpoint>/<db>`), usuário `postgres`, senha via Secrets Manager. Enviar `.jar` por `scp`, rodar `source ~/app.env && java -jar financial-boost.jar`. Flyway deve aplicar as migrações.

> Analogia rápida: a VPC é o “cofre”, o IGW é a porta controlada, o EC2 fica na sala pública (subnet pública) e o RDS permanece trancado na área privada; a role IAM é a chave que autoriza o EC2 a acessar o S3.

### Pipelines GitHub Actions
- `terraform-develop.yaml`: disparo manual (`workflow_dispatch`) → chama `terraform.yaml`, assume a role OIDC e executa `terraform init/plan/apply` com `-var-file=envs/<environment>/terraform.tfvars`.
- `deploy-develop.yaml`: trigger em `push` para `develop`; build Maven, gera `app.env`, copia jar e variáveis via `scp`, reinicia o processo no EC2 com `nohup`.

---

## Pipelines do GitHub Actions

### `terraform-develop.yaml`

- **Trigger**: `workflow_dispatch` (manual) com input `environment` (default `dev`).
- **Função**: chama o workflow reutilizável `terraform.yaml` com os parâmetros: role IAM, bucket de state e tabela Dynamo.
- **Fluxo**:
  1. `hashicorp/setup-terraform@v3` (1.8.3).
  2. Assume role `github-actions-sergioRicJr-pipeline` via OIDC.
  3. `terraform init` usando backend remoto.
  4. `terraform validate` (executado do diretório raiz — rode `cd infra` manualmente quando testar localmente).
  5. `terraform plan` + `terraform apply` com `-var-file=./envs/${environment}/terraform.tfvars`.
  6. Variável de ambiente `TF_VAR_ec2_private_key_pem` alimentada por `secrets.C2_KEY_PEM`.

### `deploy-develop.yaml`

- **Trigger**: `push` para `develop`.
- **Fluxo**:
  1. Checkout + instalação do Java 21.
  2. Assume a mesma role IAM.
  3. `mvn -B clean install`.
  4. Captura o primeiro `.jar` em `target/`.
  5. Escreve o PEM (`financialboostec2.pem`) a partir do segredo `C2_KEY_PEM`.
  6. Gera `app.env` com `DB_*`, `AWS_BUCKET_NAME`, `AWS_REGION`, `JWT_SECRET`.
  7. `scp` do jar para `${REMOTE_APP_PATH}` e do `app.env` para `~/app.env` no EC2.
  8. `ssh` para matar o processo atual (`pkill -f ${REMOTE_APP_PATH}`) e subir `nohup bash -c "set -a; source app.env; exec java -jar ..."` em background.
  9. Limpa os arquivos locais (PEM/env).

---

## Fluxo de Deploy na Nuvem

1. **Provisionar/atualizar infra**
   - Rode o workflow “DEV DEPLOY” (`terraform-develop.yaml`) escolhendo o ambiente desejado ou execute os comandos Terraform localmente.
   - Anote os outputs (`ec2_public_ip`, `rds_endpoint`, `s3_bucket_name`).

2. **Atualizar segredos**
   - `DB_URL` deve usar o endpoint do RDS (ex.: `jdbc:postgresql://financial-boost-db.xxxxx.us-east-1.rds.amazonaws.com:5432/financialboost`).
   - `S3_BUCKET` precisa bater com o bucket criado (`financial-boost-imagens`).
   - `EC2_HOST` = IP público do output.

3. **Publicar código**
   - Faça merge na branch `develop`.
   - Aguarde o workflow “Deploy DEV EC2”.
   - Verifique os logs no GitHub para confirmar `scp`, `ssh` e `nohup`.

4. **Validar no servidor**
   ```bash
   ssh -i financialboostec2.pem ec2-user@<EC2_HOST>
   ps -ef | grep financial-boost.jar
   tail -f /var/log/cloud-init-output.log  # para user data
   ```
   - O processo roda em background; logs do Spring podem ser vistos com `sudo journalctl -u` se tiver um serviço systemd (não há no momento) ou via `ps`/`lsof`.

5. **Testar**
   - Atualize o `baseUrl` da collection Postman para `http://<EC2_HOST>:8080`.
   - Rode o fluxo completo (cadastro, login, CRUDs).

---

## Observabilidade & Próximos Passos

- Ajuste `LOG_LEVEL` (INFO/WARN em produção) e habilite `infra/logging/RequestLoggingConfig` quando precisar de tracing.
- Sugerido habilitar CloudWatch Logs ou agentes no EC2 para centralizar logs.
- Próximas melhorias:
  - Expor Spring Actuator (health/metrics).
  - Implementar controllers de `balances`.
  - Adicionar testes automatizados (unitários e integração com Testcontainers).
  - Configurar aprovações em `terraform apply`.
  - Migrar `app.env` para AWS Systems Manager Parameter Store.
  - Criar classe para salvar registro em filesystem em ambiente local e parametrizar isso na aplicação

---

## Referências Rápidas

- Build local: `./mvnw clean package`
- Testes (quando existirem): `./mvnw test`
- Docker: `docker compose --env-file local.env up --build`
- Terraform (dev): `terraform plan -var-file=envs/dev/terraform.tfvars`
- Deploy manual:
  ```bash
  scp -i financialboostec2.pem target/api-0.0.1-SNAPSHOT.jar ec2-user@<EC2_IP>:/home/ec2-user/financial-boost.jar
  ssh -i financialboostec2.pem ec2-user@<EC2_IP> "source ~/app.env && nohup java -jar financial-boost.jar &"
  ```

Com isso você tem um guia único sobre o projeto, desde a preparação das ferramentas locais até o provisionamento e deploy em produção.


