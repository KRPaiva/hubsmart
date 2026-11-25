# HubSmart Brainstorm — Regras de Desenvolvimento

## Stack

- **Backend:** FastAPI + SQLAlchemy + Pydantic + SQLite por padrão.
- **Frontend:** Jinja2 + TailwindCSS (CDN) + Alpine.js (CDN) + HTMX via CDN.
- **Proibido:** npm, Node.js, package.json, React, Next.js, TypeScript e bundlers.

## Arquitetura de camadas

| Camada | Responsabilidade |
|---|---|
| Router | HTTP, request, response, redirect, status code, render de template |
| Service | Regras de negócio, fluxo e persistência quando houver lógica envolvida |
| Schema (Pydantic) | Validação de entrada e saída, específicos por caso de uso |
| Model (SQLAlchemy) | Estrutura persistida e relacionamentos |
| Template (Jinja2) | Apresentação, sem lógica complexa |

**Regra de dependência:** routers chamam services; services coordenam regras de negócio e persistência. Templates não acessam banco. JS não contém regra de negócio.

## SOLID aplicado sem abstração prematura

- **SRP:** Cada módulo, função ou classe deve ter responsabilidade clara. Não misture camadas.
- **OCP:** Só estenda quando houver variação real, como estratégias de revisão adaptativa. Sem registry, factory ou strategy para casos únicos.
- **LSP:** Prefira composição a herança. Só crie classe base com contrato reutilizável real.
- **ISP:** Use schemas específicos por operação quando fizer sentido.
- **DIP:** Queries complexas ficam em services ou funções auxiliares. Sem containers de DI ou repositories genéricos sem necessidade clara.

**Em caso de dúvida:** priorize simplicidade, legibilidade e coerência com o código existente.

## UI

- Manter **SaaS clean/light**.
- Alpine.js apenas para interações simples de tela.
- HTMX recebe HTML pré-renderizado pelo backend.

## Foco desta mini-versão

- O principal ponto de estudo é `app/services/spaced_repetition.py`.
- A persistência do estado SM2 fica em `StudyToolLink`.
- O histórico de cada revisão fica em `StudyReviewLog`.
- Use SQLite local para reduzir atrito de setup em Windows; PostgreSQL não é necessário nesta mini-versão.
- Mantenha autenticação, IA, billing, squads, kanban, mindmaps e quizzes dinâmicos fora desta pasta.

## Checklist rápido

- [ ] O router ficou sem lógica de negócio?
- [ ] A regra está no service?
- [ ] O schema é específico o suficiente?
- [ ] O template ficou sem lógica complexa?
- [ ] A solução evita abstração prematura?
- [ ] A mudança mantém zero Node/NPM?
