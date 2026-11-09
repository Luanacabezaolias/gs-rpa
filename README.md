# AccessFlow · Automação RPA

Componente de **Robotic Process Automation** do projeto AccessFlow (Global Solution FIAP 2026.2 · CitizenTech · Engenharia de Software 4º ano).

## Integrantes
| Nome completo | RM |
|---|---|
| Juliana Villalpando Maita | 99224 |
| João Victor Dos Santos Morais | 550453 |
| Luana Cabezaolias | 99320 |
| Pedro Henrique Pontes Farath | 98608 |
| Lucca Vilaça Okubo  | 551538 |

## Problema e papel da automação
O AccessFlow identifica obstáculos em passagens acessíveis de clínicas e unidades de saúde (visão computacional e robô de inspeção). Esta automação **transforma a detecção em ação**: recebe as ocorrências, evita duplicidades, define a prioridade, notifica o responsável, escala quando o prazo vence e fecha a ocorrência quando uma nova inspeção confirma que o trecho está livre.

Fluxo: `detectar → registrar → ACIONAR → RESOLVER → VERIFICAR` (a automação cobre os três últimos). Diagrama em [docs/fluxo.md](docs/fluxo.md).

## Arquitetura
```
Visão / Robô ──> API de ocorrências <──> Automação RPA (este repositório) ──> E-mail
                       │
                       └──> Painel web, Big Data (Airflow/Databricks)
```
A automação conversa com o MVP **somente pela API**, usando o contrato abaixo. Para desenvolvimento há uma API simulada em `mock_api/`.

## Estrutura
```
src/            código da automação (regras, cliente da API, notificador, orquestração)
mock_api/       API simulada para testes locais
tests/          testes automatizados (sucesso, decisão e falha)
docs/           fluxo (PDD) e roteiro do vídeo
logs/           amostras de logs e notificações (sem dados pessoais)
.env.example    modelo de configuração
```

## Como rodar
```bash
python -m venv .venv && source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env                                   # Windows: copy .env.example .env

# Terminal 1: API simulada (ou aponte ACCESSFLOW_API_URL para a API real)
python -m mock_api.server

# Terminal 2: automação (uma rodada)
python -m src.automacao
# ou repetindo a cada 60 s:
python -m src.automacao --loop 60
```
Sem `SMTP_HOST` no `.env`, as notificações são **simuladas** e gravadas em `logs/notificacoes_simuladas.log`. Para e-mail real, preencha as variáveis SMTP (use uma conta de teste).

Reiniciar o cenário de demonstração: `curl -X POST http://localhost:5000/reset`

## Como testar
```bash
python -m pytest -v
```
| Tipo | Testes |
|---|---|
| Sucesso | ocorrência nova é notificada; segunda rodada não renotifica (idempotência) |
| Decisão | duplicidade, prioridade (alta/média/baixa), inspeção livre fecha, prazo vencido escala, prazo no limite não age |
| Falha | trecho sem responsável, notificação falha sem derrubar o lote, API fora do ar aborta com erro registrado |

Teste ponta a ponta manual: suba a API simulada, rode `python -m src.automacao` e confira `curl localhost:5000/ocorrencias`. O cenário inicial cobre todos os caminhos (ver `logs/amostra_rpa.log`).

## Regras de negócio
- **Duplicidade:** mesmo trecho + mesmo tipo de objeto, original aberta e criada antes, em até 60 min.
- **Prioridade:** trecho principal = alta; caixa/carrinho = média; demais = baixa; ocorrência com 30 min ou mais sobe para alta.
- **Prazo:** alta 30 min, média 120 min, baixa 480 min. Vencido: reenvia ao responsável e ao supervisor e marca `escalada`.
- **Resolução:** inspeção com `livre = true` posterior à criação da ocorrência fecha como `resolvida`.

## Requisitos do enunciado × onde estão
| Etapa | Evidência |
|---|---|
| 01 Mapeamento | `docs/fluxo.md` |
| 02 Desenvolvimento (Python) | `src/` |
| 03 Condição e repetição | `src/automacao.py` (laços em lote e 5 decisões) |
| 04 Exceções e resiliência | `src/api_client.py` (3 tentativas), tratamento por item em `automacao.py` |
| 05 Logs e auditoria | `logs/amostra_rpa.log` (data/hora, item, resultado, erro) |
| 06 Integração com o MVP | leitura e escrita via API (`src/api_client.py`) |
| 07 Testes | `tests/` |
| 08 Documentação | este README |

## Contrato da API usado pela automação
| Método e rota | Uso |
|---|---|
| `GET /ocorrencias` | lista ocorrências |
| `PATCH /ocorrencias/{id}` | atualiza `status`, `prioridade`, `notificada_em`, `escalada_em`, `resolvida_em`, `ocorrencia_origem_id` |
| `GET /trechos/{id}` | `nome`, `principal`, `responsavel{nome,email}`, `supervisor{nome,email}` |
| `GET /inspecoes/ultima?trecho_id=` | `livre` (bool) e `em` (data/hora ISO 8601); 404 se não houver |

Ocorrência: `id, trecho_id, tipo_objeto, origem, status (nova | notificada | escalada | resolvida | duplicada), criada_em`.

## Segurança e LGPD
- Credenciais e token só em variáveis de ambiente (`.env` está no `.gitignore`).
- E-mails mascarados nos logs (`m***@exemplo.com`); dados de teste fictícios.
- Logs sem dados sensíveis; o repositório não contém dados pessoais reais.
- Notificação só ao responsável e supervisor do trecho (minimização).

## Limitações
- A API usada nos testes é simulada; a integração final depende da API do grupo seguir o contrato acima.
- Notificação por e-mail via SMTP; outros canais (Telegram, WhatsApp) não implementados.

## Links
Vídeo: https://youtu.be/HjA4EWW8qMw
Repositório: https://github.com/Luanacabezaolias/gs-rpa





