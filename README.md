# Painel de Gestão Hub Cerrado

Dashboard de indicadores estratégicos do Hub Cerrado desenvolvido com Streamlit.

## Configuração

1. Clone o repositório
2. Instale as dependências:
```bash
pip install -r requirements.txt
```

3. Configure as credenciais:
- Copie o arquivo `.env.example` para `.env`
- Edite o arquivo `.env` com suas configurações
- O usuário padrão é:
  - Username: admin
  - Password: admin123

4. Execute o aplicativo:
```bash
streamlit run painel_gestao.py
```

## Estrutura de Dados

O dashboard espera um arquivo Excel (`dados_consolidados.xlsx`) com as seguintes colunas:
- Data
- Indicador
- Valor
- Meta (opcional)

## Deploy no Streamlit Cloud

1. Faça fork do repositório
2. Conecte ao Streamlit Cloud
3. Configure as seguintes variáveis de ambiente:
   - `STREAMLIT_APP_NAME`
   - `CONFIG_PATH`

## Segurança

- As credenciais são armazenadas de forma segura usando hashing
- O acesso é controlado por autenticação
- Sessões expiram após 30 dias de inatividade 