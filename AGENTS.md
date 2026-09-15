# AGENTS.md — RAG_base

Постоянные инструкции проекта для AI-коддинг-агента (OpenCode и совместимые),
загружаются автоматически в каждой сессии в этом репозитории.

## 0. Роль и правила работы

Ты — Senior AI/Backend-инженер, работающий в паре со мной над этим
репозиторием. Это учебный RAG-проект (FastAPI + ChromaDB +
SentenceTransformers + Ollama + Streamlit), который нужно довести до уровня
**качественного портфолио-проекта для трудоустройства AI Engineer'ом**.

Правила на каждую сессию:

1. Перед началом работы посмотри раздел **8. Roadmap** — найди первый пункт
   без `[x]` и её же сверь с `git log`, чтобы понять реальное состояние
   репозитория (roadmap мог быть отмечен, а коммит не запушен, или наоборот).
2. Работай **по одной задаче roadmap за раз**, если явно не попросили иначе.
   Не забегай вперёд и не делай сразу несколько пунктов.
3. По завершении задачи: прогони линтер/тесты → отметь пункт в roadmap как
   `[x]` → сделай **отдельный коммит** в стиле Conventional Commits (раздел 7)
   → **запушь** в удалённую ветку.
4. Не объединяй несколько пунктов roadmap в один коммит. Не делай финальный
   "залповый" коммит со всем проектом.
5. Если задача неоднозначна или требует решения из раздела **10. Открытые
   вопросы** — коротко спроси меня перед реализацией, не выбирай молча.
6. После коммита кратко отчитайся, что сделано и какой пункт roadmap следующий.

---

## 1. Цель проекта

Превратить базовый учебный RAG в проект, который на собеседовании
демонстрирует:

- умение проектировать **расширяемую архитектуру** (паттерны, а не "всё в
  одном файле");
- владение современным стеком RAG: гибридный поиск, реранкинг, multi-format
  ingestion (включая веб и видео);
- умение строить multi-user систему с аутентификацией и персистентностью;
- provider-agnostic слой LLM с выбором модели пользователем;
- полноценный, аккуратный веб-интерфейс (не Streamlit-прототип);
- инженерную культуру: тесты, CI, Docker, логирование, осмысленный git-flow.

---

## 2. Текущее состояние (baseline)

Зафиксировано аудитом репозитория на момент старта:

- **Чанкинг**: ручной сплит `.docx` по маркеру `##`, без учёта токенов,
  без overlap, без поддержки других форматов.
- **Vector store**: `VectorStore` в одном классе инициализирует модель
  эмбеддингов, ChromaDB-клиента и логику чанкинга — нет разделения
  ответственности, невозможно подменить провайдера без переписывания класса.
- **LLM**: жёстко зашитая Ollama-модель из `.env`; есть мёртвый
  закомментированный код под OpenAI-совместимый эндпоинт; выбора модели нет.
- **Стриминг**: фейковый — ответ уже полностью посчитан, на фронт выводится
  посимвольно через `time.sleep`.
- **История чата**: только `st.session_state`, теряется при обновлении
  страницы; персистентности нет вообще.
- **UI**: Streamlit, минимальная кастомизация через CSS-строку.
- **Auth**: в `.env` есть неиспользуемая переменная `APP_PASSWORD`, реальной
  аутентификации/мультипользовательности нет.
- **Качество/DevOps**: нет тестов, CI, Docker, логирования, реранкинга,
  metadata-фильтрации — всё это в README числится как "будущие улучшения".

---

## 3. Целевая архитектура

Используем **Hexagonal Architecture (Ports & Adapters)** с явными
**Strategy** (взаимозаменяемые реализации) и **Factory** (выбор реализации
по конфигу/типу источника) паттернами. Это даёт ровно то, что нужно —
"удобно модифицировать": подключить новый LLM-провайдер, загрузчик
документов или векторную БД — значит добавить один адаптер, не трогая
остальной код.

```
┌─────────────────────────────────────────────────────────────┐
│  API layer (FastAPI routers)  — тонкий, только HTTP <-> use-case │
├─────────────────────────────────────────────────────────────┤
│  Application layer (use-cases)                                │
│  IngestDocumentUseCase, AnswerQueryUseCase, ChatUseCase        │
├─────────────────────────────────────────────────────────────┤
│  Domain layer — чистый Python, без фреймворков                 │
│  Document, Chunk, ChatMessage, User (dataclasses/pydantic)     │
├─────────────────────────────────────────────────────────────┤
│  Ports (Protocol/ABC)                                          │
│  DocumentLoader · Chunker · EmbeddingProvider ·                │
│  VectorStoreRepository · LLMProvider · ChatRepository           │
├─────────────────────────────────────────────────────────────┤
│  Adapters (infrastructure)                                     │
│  DoclingLoader · YouTubeLoader · HybridChunkerAdapter ·         │
│  BgeM3EmbeddingProvider · QdrantVectorStore ·                  │
│  OpenRouterProvider / AnthropicProvider / OllamaProvider ·      │
│  PostgresChatRepository / PostgresUserRepository                │
└─────────────────────────────────────────────────────────────┘
```

Composition root (сборка зависимостей) — отдельный модуль
`app/core/container.py`, а не разбросанные `@lru_cache` функции. Роутеры
получают готовые use-case'ы через `Depends`.

---

## 4. Технологический стек (целевой)

| Слой | Сейчас | Предлагается |
|---|---|---|
| Векторная БД | ChromaDB (локальный файл) | **Qdrant** (self-hosted в docker-compose), dense+sparse векторы, payload-индексы |
| Эмбеддинги | `intfloat/multilingual-e5-base` | **`BAAI/bge-m3`** — dense + sparse одним проходом, сильный мультиязычный (включая RU) |
| Реранкинг | нет | `BAAI/bge-reranker-v2-m3` (cross-encoder, мультиязычный) |
| Чанкинг | ручной regex-сплит, только docx | **Docling** (`DocumentConverter` + `HybridChunker`, token-aware, сохраняет структуру/таблицы) для pdf/docx/pptx/xlsx/html/md/изображений (OCR); отдельный **YouTubeLoader** для видео |
| Backend framework | FastAPI | FastAPI (оставляем) |
| Relational DB | нет | **PostgreSQL** + SQLAlchemy 2.0 (async) + Alembic-миграции |
| Очередь задач | нет | Redis + **arq/RQ** для асинхронного ingestion (парсинг Docling и особенно транскрипция видео — долгие операции, не должны блокировать API) |
| LLM-слой | Ollama, жёстко зашит | Provider-abstraction: **OpenRouter** (один ключ → GPT/Claude/Gemini/Llama/DeepSeek — удобно для "выбора модели"), **Anthropic SDK** нативно, **Ollama** как локальный/офлайн адаптер |
| Стриминг | fake char-by-char | настоящий **SSE**-стриминг токенов от провайдера |
| Auth | нет | JWT (access+refresh), bcrypt/passlib |
| Frontend | Streamlit | **Next.js (App Router) + TypeScript + Tailwind + shadcn/ui**, минималистичный дизайн |
| Dev/Deploy | Makefile | `docker-compose.yml`: backend, frontend, qdrant, postgres, redis — один `docker compose up` |
| Тесты | нет | `pytest` + `httpx.AsyncClient`, unit + integration |
| Lint/format | нет | `ruff` (+ `ruff format`), `pre-commit` |
| CI | нет | GitHub Actions: lint + tests на каждый push/PR |
| Observability | нет | `structlog`, request-id middleware, опционально RAGAS-эвалюация retrieval |

---

## 5. Детальные требования по блокам

### 5.1 Ingestion pipeline

- Единая точка входа `POST /documents`: файл (multipart) **или** `{"url": "..."}`
  в теле — источник любой: файл, ссылка на статью/страницу, ссылка на YouTube.
- `LoaderFactory` определяет загрузчик по типу источника:
  - YouTube-паттерн URL → `YouTubeLoader` (`yt-dlp` + субтитры через
    `youtube-transcript-api`; если субтитров нет — fallback на
    `faster-whisper` для транскрипции аудио) → результат нормализуется в
    markdown с таймкодами как метаданные;
  - прочий URL (статья/веб-страница/PDF по ссылке) → Docling принимает URL
    напрямую;
  - локальный файл (pdf/docx/pptx/xlsx/html/md/изображение) → Docling
    `DocumentConverter`.
- Чанкинг — Docling `HybridChunker`: учитывает токенизатор эмбеддинг-модели,
  сохраняет структуру (заголовки, таблицы), в метаданные чанка пишем
  `source_id`, `title`, `section`, диапазон токенов/символов.
- Ingestion выполняется **асинхронно** через очередь задач; статус
  (`pending/processing/done/error`) хранится в Postgres и отдаётся фронту
  (поллинг или SSE).
- Дедупликация по хэшу содержимого чанка — не переэмбеддивать то, что не
  изменилось (идея уже была в исходном коде через `hashlib`, довести до ума).

### 5.2 Векторное хранилище — Qdrant

- Один поднятый через docker-compose инстанс Qdrant с volume.
- **Одна коллекция** с payload-полями `user_id`/`workspace_id`,
  `document_id`, `chunk_id`, `source_type`, `title`, `url`, `created_at` —
  фильтрация по пользователю на уровне запроса. Проще в эксплуатации, чем
  коллекция на каждого пользователя; про масштабирование — отдельная заметка
  в README ("если пользователей станет много — переход на collection per
  tenant").
- Именованные векторы: dense (`bge-m3` dense) + sparse (`bge-m3` sparse или
  `Qdrant/bm25`) в одной точке; поиск через Query API с `prefetch` по обоим
  и **RRF-фьюжн**.
- После фьюжна — реранкинг top-30/50 кандидатов кросс-энкодером
  `bge-reranker-v2-m3`, в контекст LLM идёт top-5.
- Payload-индексы на `user_id` и `document_id` для быстрой фильтрации.

### 5.3 LLM-слой и выбор модели

- Порт `LLMProvider.generate(messages, stream=True) -> AsyncIterator[str]`.
- Адаптеры: `OpenRouterProvider` (OpenAI-совместимый `/chat/completions`,
  модель выбирается строкой model-id — так один ключ даёт доступ к десяткам
  моделей), `AnthropicProvider` (нативный SDK), `OllamaProvider` (локальный
  fallback, оставляем текущую интеграцию).
- Реестр доступных моделей (`models.yaml` или таблица в БД): id, отображаемое
  имя, провайдер, контекстное окно — фронт строит выпадающий список из
  `GET /models`.
- Выбор модели сохраняется вместе с каждым сообщением в истории (видно, какая
  модель отвечала).
- **Опционально (фаза 2, не блокирует v1)**: BYOK — пользователь может
  вставить свой API-ключ в настройках, хранится зашифрованным (Fernet) в
  Postgres, используется вместо системного ключа.

### 5.4 Чаты и персистентность

Черновая схема Postgres:

```
users(id, email, hashed_password, created_at)
chats(id, user_id, title, created_at, updated_at)
messages(id, chat_id, role, content, model_used, sources_json, created_at)
documents(id, user_id, source_type[file|url|youtube], origin, status, created_at)
```

(сами чанки живут в Qdrant; `documents` только трекает ingestion.)

- CRUD чатов: создать/список/переименовать/удалить, список сообщений,
  отправка сообщения → SSE-стрим ответа.
- Источники (citations): каждое сообщение ассистента хранит, из каких
  чанков/документов взят ответ → в UI сворачиваемый блок "источники".

### 5.5 Frontend

- Next.js + TypeScript + Tailwind + shadcn/ui. Минимализм: светлая тема по
  умолчанию, много воздуха, без визуального шума — по духу ближе к
  Claude/Perplexity, чем к типичному Streamlit-дашборду.
- Страницы: `/chat` (основная), `/documents` (загрузка и статус базы знаний),
  `/login`, `/register`, `/settings` (профиль, опционально BYOK).
- Layout: левый сайдбар (список сохранённых чатов + "новый чат" + ссылка на
  документы), основная панель чата, выбор модели сверху справа, поле ввода
  с возможностью прикрепить файл или вставить ссылку.
- Стриминг — SSE (`EventSource`) либо Vercel AI SDK (`useChat`).
- Источники под ответом — компактные чипы, по клику показывают исходный
  фрагмент текста.
- Адаптивность и базовая доступность (семантическая разметка, фокус-стейты).

### 5.6 Auth и мультипользовательность

- JWT access+refresh, пароли — bcrypt.
- Изоляция данных: документы и чаты фильтруются по `user_id` на каждом
  запросе, это явно покрыто тестами.
- Концепция "workspace" (общая база знаний на команду) — зафиксировать как
  возможное расширение, в scope v1 не включать, чтобы не размывать фокус.

### 5.7 Качество, тесты, DevOps

- `pytest`: unit-тесты (чанкер, роутинг `LoaderFactory`, сборка промпта),
  integration-тесты (FastAPI `TestClient`/`AsyncClient` против реального
  Qdrant/Postgres в тестовом docker-compose или testcontainers).
- `ruff` + `ruff format`, `pre-commit`.
- GitHub Actions: на каждый push/PR — lint + тесты (опционально сборка
  Docker-образов).
- `docker-compose.yml`: backend, frontend, qdrant, postgres, redis — весь
  стек одной командой `docker compose up --build`.
- `structlog` + request-id middleware; базовый rate limiting (`slowapi`) на
  эндпоинте чата.
- README переписать полностью: архитектурная диаграмма (mermaid), quick
  start, скриншоты/GIF, раздел "почему выбран именно этот стек" — это тоже
  часть портфолио, рекрутеры читают README.

### 5.8 Опционально, если останется время

- Эвалюация retrieval через **RAGAS** (`faithfulness`, `answer_relevancy`,
  `context_precision`) на небольшом golden-сете вопросов по документам
  ДагГАУ — сильный аргумент на собеседовании ("как вы измеряли качество RAG").
- Query rewriting / multi-query expansion для неоднозначных вопросов.
- HyDE как переключаемая опция.
- Простой admin-дашборд: статистика ingestion, расход токенов по
  пользователям.

---

## 6. Структура репозитория (целевая)

```
RAG_base/
├── backend/
│   ├── app/
│   │   ├── domain/            # сущности, чистый Python
│   │   ├── ports/              # Protocol/ABC интерфейсы
│   │   ├── application/        # use-cases
│   │   ├── adapters/
│   │   │   ├── loaders/        # docling_loader.py, youtube_loader.py
│   │   │   ├── chunkers/
│   │   │   ├── embeddings/
│   │   │   ├── vector_store/   # qdrant_store.py
│   │   │   ├── llm/            # openrouter.py, anthropic.py, ollama.py
│   │   │   └── db/             # postgres-репозитории
│   │   ├── api/                # FastAPI роутеры (тонкие)
│   │   ├── core/                # config, container (DI), security
│   │   └── main.py
│   ├── alembic/
│   ├── tests/
│   └── pyproject.toml
├── frontend/                   # Next.js app
├── eval/                       # (опц.) RAGAS golden-сет и скрипт оценки
├── docker-compose.yml
├── .github/workflows/ci.yml
└── README.md
```

---

## 7. Git-процесс (обязательное требование)

- **Conventional Commits**: `feat:`, `fix:`, `refactor:`, `docs:`, `test:`,
  `chore:`, `ci:`. Пример: `feat(vector-store): add Qdrant hybrid search adapter`.
- Одна задача из roadmap (раздел 8) = один коммит (или несколько тесно
  связанных мелких коммитов внутри задачи, если это упрощает ревью).
- После каждой задачи:
  ```
  git add -A
  git commit -m "feat(...): ..."
  git push
  ```
- Рекомендуется ветка на фичу + PR (даже self-merge) — это тоже демонстрирует
  рабочий процесс рецензентам; прямые коммиты в `main` тоже допустимы для
  соло-проекта, если время поджимает.
- Не делать финальный "залповый" коммит со всем проектом — история должна
  быть читаемой историей разработки, это то, что смотрят рекрутеры/техлиды.

---

## 8. Roadmap задач (каждый пункт — отдельный коммит)

Отмечай `[x]` сразу в том же коммите, которым закрываешь пункт.

- [x] 1. `chore`: настройка репозитория — uv/poetry, `ruff`/`pre-commit`, обновлённый `.env.example`, базовая структура папок под чистую архитектуру.
- [x] 2. `feat(domain)`: доменные сущности и порты — `Document`, `Chunk`, `ChatMessage`; интерфейсы `DocumentLoader`, `Chunker`, `EmbeddingProvider`, `VectorStoreRepository`, `LLMProvider`, `ChatRepository`.
- [x] 3. `feat(infra)`: `docker-compose.yml` — Qdrant, Postgres, Redis.
- [x] 4. `feat(ingestion)`: адаптер `DoclingLoader` (pdf/docx/pptx/xlsx/html/md/изображения) + `HybridChunker`.
- [x] 5. `feat(ingestion)`: `YouTubeLoader` (`yt-dlp` + `youtube-transcript-api`, fallback `faster-whisper`).
- [x] 6. `feat(ingestion)`: `LoaderFactory` + асинхронная очередь (arq/RQ) + таблица `documents` со статусами.
- [x] 7. `feat(vector-store)`: `QdrantVectorStoreRepository` — dense+sparse (`bge-m3`), payload-фильтрация по `user_id`.
- [x] 8. `feat(retrieval)`: гибридный поиск (RRF) + реранкинг (`bge-reranker-v2-m3`).
- [x] 9. `feat(llm)`: провайдеры `OpenRouterProvider`, `AnthropicProvider`, `OllamaProvider` + `LLMProviderFactory` + реестр моделей.
- [x] 10. `feat(api)`: настоящий SSE-стриминг вместо fake streaming.
- [x] 11. `feat(auth)`: регистрация/логин, JWT, хэширование паролей, middleware авторизации.
- [x] 12. `feat(db)`: async SQLAlchemy-модели + Alembic-миграции (`users`, `chats`, `messages`, `documents`).
- [x] 13. `feat(api)`: CRUD чатов и сообщений, сохранение источников (citations) к ответам.
- [x] 14. `feat(api)`: эндпоинты управления документами (файл/URL/YouTube), статус обработки.
- [x] 15. `feat(frontend)`: каркас Next.js + Tailwind + shadcn/ui, страницы авторизации.
- [x] 16. `feat(frontend)`: чат со стримингом (SSE/`useChat`), выбор модели, отображение источников.
- [x] 17. `feat(frontend)`: страница управления базой знаний (загрузка файлов/ссылок, статусы, удаление).
- [x] 18. `feat(frontend)`: сайдбар с сохранёнными чатами, финальный минималистичный дизайн, адаптивность.
- [x] 19. `test`: unit + integration тесты (`pytest`) на ключевые сценарии.
- [ ] 20. `ci`: GitHub Actions — lint + тесты на каждый push.
- [ ] 21. `feat(observability)`: структурное логирование, rate limiting.
- [ ] 22. `docs`: полный README — архитектурная диаграмма (mermaid), скриншоты, инструкция по запуску.
- [ ] 23. *(опционально)* `feat(eval)`: RAGAS-оценка retrieval на golden-сете вопросов.

---

## 9. Критерии готовности (Definition of Done)

- [ ] `docker compose up` поднимает весь стек одной командой.
- [ ] Поддержано минимум 5–6 форматов источников, включая произвольный URL и YouTube.
- [ ] Гибридный поиск + реранкинг работают и заметно улучшают релевантность (есть пример "до/после" в README).
- [ ] Минимум два LLM-провайдера с переключением модели прямо в UI.
- [ ] Чаты сохраняются в БД и переживают перезагрузку страницы.
- [ ] Есть аутентификация и изоляция данных между пользователями.
- [ ] Есть тесты и зелёный CI.
- [ ] README рассказывает архитектурную историю проекта, а не только "как запустить".
- [ ] История git показывает поэтапную осмысленную разработку.

---

## 10. Открытые вопросы (решить по ходу или сразу зафиксировать)

- **Next.js vs Vite+React**: Next.js выглядит весомее в резюме, но добавляет
  сложности. Если критично время — можно упростить до Vite+React+Tailwind без
  потери сути архитектуры бэкенда.
- **BYOK**: красивая фича, но требует шифрования ключей. Для v1 достаточно
  единого системного ключа (OpenRouter) с выбором модели; BYOK — фаза 2.
- **Qdrant self-hosted (docker) vs Qdrant Cloud**: self-host честнее
  показывает DevOps-навык и используется в roadmap по умолчанию; Cloud
  free-tier можно рассмотреть отдельно для удобства демо на созвоне с
  рекрутером.
- **Хостинг демо**: решить в конце — например, Vercel для фронта +
  Fly.io/Render/VPS для backend+Qdrant+Postgres, чтобы дать рекрутерам живую
  ссылку, а не только репозиторий.
