# Bitcoin Python Scripts

Scripts Python para processamento de endereços Bitcoin e integração com APIs.

## 📋 Requisitos

- Python 3.8+
- GPU compatível
- Conexão com Internet

## 🚀 Instalação

1. Clone o repositório

git clone https://github.com/seu-usuario/btcpythonscripts.git
cd btcpythonscripts

2. Instale as dependências

pip install -r requirements.txt

## ⚙️ Configuração

Crie um arquivo `.env` com:

env
API_URL=sua_url_api
POOL_TOKEN=seu_token
ADDITIONAL_ADDRESS=endereco_adicional
BATCH_SIZE=10
SLEEP_TIME=5

## 💻 Uso

Execute o script principal:

python pool.py

Para obter a chave pública:

python get_public_key.py


## 🔧 Configurações da GPU

Ajuste as configurações no `config.py`:

python
GPU_SETTINGS = {
"threads": "0",
"gpu_id": "0",
"grid_size": "1536"
}
## ✨ Funcionalidades

- Processamento de endereços Bitcoin
- Integração com API Mempool.space
- Suporte a GPU para processamento
- Sistema de retry automático
- Logging estruturado
- Processamento em lotes
- Validação de endereços
- Controle de estado do programa
- Tratamento de exceções robusto

## 📦 Dependências

- requests>=2.31.0
- tenacity>=8.2.3
- python-dotenv>=1.0.0

## 🔍 Recursos

- Validação de endereços Bitcoin
- Processamento em lotes
- Sistema de retry automático
- Logging detalhado
- Controle de estado do programa
- Tratamento de exceções robusto
- Integração com APIs externas
- Suporte a múltiplas GPUs

## 📝 Licença

Este projeto está sob a licença MIT.

## 🤝 Contribuindo

1. Faça um Fork do projeto
2. Crie uma Branch para sua Feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a Branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request
