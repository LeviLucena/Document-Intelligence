# Document Intelligence API

![Python](https://img.shields.io/badge/Python_3-3776AB?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![Pydantic](https://img.shields.io/badge/Pydantic_v2-E92063?style=for-the-badge&logo=pydantic&logoColor=white)
![NumPy](https://img.shields.io/badge/NumPy-013243?style=for-the-badge&logo=numpy&logoColor=white)
![Amazon Bedrock](https://img.shields.io/badge/Amazon_Bedrock-FF9900?style=for-the-badge&logoColor=white)
![React](https://img.shields.io/badge/React_18-61DAFB?style=for-the-badge&logo=react&logoColor=black)
![Vite](https://img.shields.io/badge/Vite_6-646CFF?style=for-the-badge&logo=vite&logoColor=white)
![Lucide](https://img.shields.io/badge/Lucide_Icons-F56040?style=for-the-badge&logo=lucide&logoColor=white)
![Pytest](https://img.shields.io/badge/Pytest-0A9EDC?style=for-the-badge&logo=pytest&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)

![alt text](https://i.ibb.co/N2vpdXJV/image.png)

RAG para documentos empresariais: envie PDFs, faça perguntas em linguagem natural e receba respostas **com citações** (documento + página). FastAPI + Amazon Bedrock, com métricas de latência e consumo de tokens por pergunta.

![alt text](https://i.ibb.co/Vcntjspx/image.png)


## Rodar (sem Docker)

```powershell
py -3.14 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

Abra http://127.0.0.1:8000 (interface) ou http://127.0.0.1:8000/docs (Swagger).

## Frontend (React + Vite)

O código está em `frontend/`; o build (`app/static/`) já vem pronto e é servido pelo FastAPI, então **não precisa de Node para rodar**. Para mexer na interface:

```powershell
cd frontend
npm install
npm run dev      # http://localhost:5173, com proxy para a API em :8000
npm run build    # gera app/static/
```

## Providers

| `PROVIDER` | O que faz | Custo |
|---|---|---|
| `local` (padrão) | Embeddings por hash + resposta extrativa. Demonstra o fluxo inteiro sem AWS. | zero |
| `bedrock` | Embeddings Titan v2 + geração via **Converse API** (Claude Haiku). | pago por uso |

Para usar o Bedrock: copie `.env.example` para `.env`, defina `PROVIDER=bedrock`, configure as credenciais AWS (`aws configure`) e habilite o acesso aos modelos no console do Bedrock.

## API

| Método | Rota | Descrição |
|---|---|---|
| POST | `/documents` | Upload de PDF (indexa em trechos com página) |
| GET | `/documents` | Lista documentos indexados |
| DELETE | `/documents/{name}` | Remove documento |
| POST | `/ask` | `{"question": "...", "top_k": 4}` → resposta, `citations[]`, `metrics` |
| GET | `/health` | Status e provider ativo |

Exemplo de `metrics` (também registrado em log a cada pergunta):

```json
{"provider":"bedrock","retrieval_ms":212.4,"generation_ms":1480.2,"total_ms":1692.6,
 "input_tokens":812,"output_tokens":146,"estimated_cost_usd":0.000385}
```

Os preços ficam em `app/config.py` (`price_in_per_1k` / `price_out_per_1k`); confira a tabela vigente da AWS.

## Decisões de arquitetura

- **RAG próprio em vez de Knowledge Bases / `RetrieveAndGenerate`:** esse caminho exige uma Knowledge Base, que costuma depender de OpenSearch Serverless (custo fixo mensal). Aqui o índice é NumPy em disco (`data/`), e o código mostra cada etapa: extração → chunking → embeddings → busca por cosseno → prompt com trechos numerados → citações `[n]`.
- **Interface `Provider`:** trocar local ↔ Bedrock não muda o resto do código.
- **Prompt ancorado:** o modelo só pode usar os trechos fornecidos e deve citar `[n]`; sem base suficiente, diz que não encontrou.

## Testes

```powershell
.\.venv\Scripts\python.exe -m pytest
```

O provider Bedrock é testado com `botocore.Stubber` (sem chamar a AWS).

## Docker (opcional)

```powershell
docker build -t docintel . ; docker run -p 8000:8000 docintel
```

## Limitações

PDFs escaneados (sem texto) não são suportados — seria preciso OCR (ex.: Amazon Textract). O índice em memória serve para centenas de documentos, não milhões.
