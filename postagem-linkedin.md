🚀 Compartilhando um projeto que desenvolvi focando em **Infraestrutura como Código (IaC)** com Terraform!

Acabei de finalizar o **FinancialBoost API**, uma API financeira em Spring Boot que me permitiu explorar profundamente o provisionamento de infraestrutura na AWS usando Terraform.

### 🏗️ O que foi provisionado:
- Rede completa (VPC, subnets públicas/privadas, IGW, route tables)
- EC2 com Amazon Linux 2023 e Java 21
- RDS PostgreSQL 15.7 em subnet privada
- S3 bucket para armazenamento de comprovantes
- Security Groups e IAM roles configurados
- CI/CD com GitHub Actions usando OIDC para autenticação segura

### 📝 Uma observação importante:

É importante deixar claro que **esta não é a melhor forma de fazer deploy de um projeto em produção**. Utilizei EC2 com deploy direto via SSH/SCP apenas para fins de estudo e aprendizado de Terraform.

Em projetos reais, utilizo e recomendo:
- ✅ Imagens Docker containerizadas
- ✅ Orquestração com Kubernetes
- ✅ Serviços gerenciados da AWS
- ✅ Deploy automatizado com rollback capabilities

Este projeto foi uma excelente oportunidade para entender na prática como o Terraform funciona, desde a criação de recursos até o gerenciamento de state remoto com S3 e DynamoDB para locking.

### 📚 Tutorial completo:

O tutorial completo de cada etapa está documentado detalhadamente no README do repositório, incluindo configuração de ambiente local, execução com Docker e Maven, provisionamento manual e automatizado via GitHub Actions, variáveis de ambiente, segredos e troubleshooting.

### 🔮 Próximos projetos:

Estou planejando uma série de projetos e postagens sobre:

1. **System Design de serviços relacionados a saldo financeiro e transações** - arquiteturas escaláveis, padrões de consistência e alta disponibilidade para sistemas financeiros

2. **Projetos com Kubernetes** - migração para EKS, Helm charts, service mesh e observabilidade

Fiquem ligados para os próximos conteúdos! 🚀

#Terraform #AWS #InfrastructureAsCode #DevOps #SpringBoot #CloudComputing #SystemDesign #Kubernetes
