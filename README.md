# HubSmart Brainstorm

Mini-versão didática do HubSmart focada em flashcards e repetição espaçada SM2.

## Objetivo

Esta pasta existe para estudantes alterarem o algoritmo em `app/services/spaced_repetition.py` e testarem adaptações ao usuário sem carregar billing, IA, squads, kanban, mindmaps, profile ou Playwright.

## Stack

- FastAPI, SQLAlchemy, Pydantic e SQLite local por padrão.
- Jinja2, TailwindCSS via CDN, Alpine.js via CDN e HTMX via CDN.
- Zero Node/NPM, sem bundler, sem React, sem TypeScript.

## Pré-requisitos

- Requisito mínimo inicial: Python 3.12, 3.13 ou 3.14 instalado.
- O Poetry será instalado usando o próprio Python antes de rodar o projeto.
- No Windows, use PowerShell.
- Não é necessário instalar Docker, PostgreSQL, Node.js ou NPM para esta mini-versão.

Por que usamos essas ferramentas:

- Python executa o projeto FastAPI e as ferramentas de banco/teste.
- `pipx` instala programas Python de linha de comando em ambientes isolados. Assim o Poetry não fica misturado com as dependências do projeto.
- Poetry cria o ambiente virtual do projeto e instala exatamente as dependências registradas em `poetry.lock`.
- SQLite evita instalação de banco separado. O banco vira apenas um arquivo local, `hubsmart_brainstorm.db`.

Para instalar o Poetry no Windows PowerShell com `pipx`:

```powershell
py -m pip install --user pipx
py -m pipx ensurepath
py -m pipx install poetry
```

Depois feche e abra o PowerShell novamente e confira:

```powershell
poetry --version
```

No Linux/macOS com `pipx`:

```bash
python3 -m pip install --user pipx
python3 -m pipx ensurepath
python3 -m pipx install poetry
```

Se `pipx` já estiver instalado, basta rodar `pipx install poetry`.

## Arquitetura

- `app/routers/`: apenas HTTP e renderização.
- `app/services/`: regras de negócio e persistência.
- `app/schemas/`: validação Pydantic.
- `app/models/`: SQLAlchemy.
- `templates/`: apresentação Jinja2.

## Fluxo SM2

1. Um deck é criado em `/workspace/flashcards`.
2. Cada flashcard criado gera um `StudyToolLink` vencido imediatamente.
3. `/workspace/reviews` exibe a fila vencida.
4. Ao avaliar um cartão, `study_reviews.grade_flashcard_review()` chama `spaced_repetition.apply_review()`.
5. O próximo estado é salvo em `StudyToolLink` e o histórico em `StudyReviewLog`.

## Ajuste contextual experimental

Na tela de revisão, o estudante pode marcar **“Preciso revisar este conteúdo antes”**.
Essa opção envia o contexto `review_earlier` ao serviço de revisão. O SM-2 calcula
primeiro o intervalo normalmente; em seguida, a camada contextual reduz esse
intervalo em aproximadamente 25%, respeitando o mínimo de um dia.

Quando a opção não é marcada, o comportamento original do SM-2 é preservado.
O contexto utilizado fica registrado no campo `answers` de `StudyReviewLog`.

**Limitação atual:** esta mini-versão ainda não possui entidades próprias para
matérias, provas, atividades ou agenda acadêmica. Portanto, o ajuste contextual
é uma escolha manual do estudante e não representa ainda o cruzamento automático
entre agenda e desempenho por matéria. Essa integração depende do mapeamento e
da implementação desses dados em uma etapa posterior.

## Rodar localmente no Linux/macOS

```bash
cp .env.example .env
make setup
make seed
make dev
```

Acesse `http://localhost:8000/workspace`.

O banco fica no arquivo `hubsmart_brainstorm.db` dentro desta pasta.

## Rodar localmente no Windows

No PowerShell:

```powershell
copy .env.example .env
poetry install --with dev
poetry run alembic upgrade head
poetry run python -m scripts.seed_dev
poetry run uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Acesse `http://localhost:8000/workspace`.

## Comandos úteis

```bash
make setup
make seed
make dev
make test
make lint
make clean
```

`make clean` remove caches e os arquivos SQLite locais.

## Testes

```bash
make test
```

Os testes usam `hubsmart_brainstorm_test.db` por padrão. O teste unitário de SM2 também pode ser rodado isoladamente:

```bash
make test-unit
```
