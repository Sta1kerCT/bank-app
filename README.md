# Bank App

Простое банковское приложение на Python: API-сервер, Kafka-консюмер, PostgreSQL, мониторинг.

## Запуск всей системы

```bash
docker compose up
```

Поднимаются:

- **PostgreSQL** — база данных (порт 5432)
- **Zookeeper + Kafka** — брокер сообщений
- **server** — FastAPI API (порт 8000): счета и транзакции
- **consumer** — обработка транзакций из Kafka (обновление балансов)
- **Prometheus** — метрики (порт 9090)
- **Grafana** — дашборды (порт 3000)
- **client** — демо-клиент (опционально)

Сценарий: вызов ручки на сервере (например `POST /transactions/`) создаёт транзакцию, сервер отправляет событие в Kafka, консюмер обрабатывает его и обновляет балансы в PostgreSQL.

## API

- `GET /` — приветствие
- `GET /health` — проверка здоровья
- `GET /metrics` — метрики Prometheus
- `POST /accounts/` — создать счёт
- `GET /accounts/`, `GET /accounts/{account_number}` — список счётов / один счёт
- `POST /transactions/` — создать транзакцию (DEPOSIT / WITHDRAW / TRANSFER)
- `GET /transactions/{id}` — статус транзакции

## Тесты и покрытие

- Покрытие по проекту: **не менее 90%**.
- В CI (GitHub Actions) запускаются тесты и выводится отчёт покрытия.

### Локально

**Сервер:**

```bash
cd server
pip install -r requirements.txt
pytest tests/ -v --cov=app --cov-report=term-missing --cov-fail-under=90
```

**Консюмер:**

```bash
cd consumer
pip install -r requirements.txt
pytest tests/ -v --cov=app --cov-report=term-missing --cov-fail-under=90
```

## CI

- **Python Tests & Coverage** (`python-tests.yml`) — pytest для server и consumer с покрытием ≥90%; в логе шага видно отчёт покрытия.


