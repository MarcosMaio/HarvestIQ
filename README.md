# HarvestIQ: Sugarcane Harvest Optimization

## Overview

**HarvestIQ** is an API‑driven solution designed to optimize sugarcane harvest operations by quantifying losses, calculating efficiency metrics, and delivering actionable insights. Built with Python and Docker, it provides a clear, data‑driven workflow that:

- Receives detailed harvest data via a RESTful POST endpoint.
- Validates and processes inputs using Pydantic models and subalgorithms.
- Persists records both locally (JSON) and in an Oracle database.
- Computes key performance indicators (KPIs) and generates alerts/recommendations.
- Exposes a GET endpoint for retrieving historical harvest records.

This project addresses the complexity of agribusiness data management—specifically the "pain point" of high sugarcane harvest losses—by leveraging automation, structured data handling, and cloud‑native containerization.

---

## Architecture & Docker

The solution is containerized via Docker:

- **Oracle container**: Runs Oracle XE (e.g., `gvenzl/oracle-xe:21-slim`), exposing port `1521`. It provides the pluggable database `XEPDB1`.
- **App container**: Hosts the Flask application. It connects to the Oracle container over the Docker network, and mounts a volume for local JSON storage (`harvest_history.json`).

### Under the hood
When you run `docker-compose up`:

- The Oracle image initializes, creates the PDB and default users.
- The Flask image builds from `backend/Dockerfile`, installs dependencies, and starts on port `8000` (or `$PORT`).
- Networking and environment variables ensure seamless connectivity (`ORACLE_HOST=db`, `ORACLE_USER`, etc.).

---

## Getting Started

### Prerequisites

- Docker & Docker Compose installed on your machine.
- Git to clone the repository.

### Setup

1. Clone the repo:

```bash
git clone https://github.com/MarcosMaio/HarvestIQ.git
cd HarvestIQ
```

2. Define environment variables in a `.env` file at project root:

```env
ORACLE_USER=harvest_user
ORACLE_PASSWORD=harvest_pass
ORACLE_HOST=db
ORACLE_PORT=1521
ORACLE_SERVICE_NAME=XEPDB1
HISTORY_FILE_PATH=/app/harvest_history.json
PORT=8000
FLASK_DEBUG=true
```

3. Launch containers:

```bash
docker-compose up --build
```

4. Initialize database schema (once):

```bash
docker exec -it harvestiq_db_1 sqlplus sys/Oracle123@//localhost:1521/XEPDB1 as sysdba
```

Inside SQL*Plus:

```sql
CREATE USER harvest_user IDENTIFIED BY harvest_pass;
GRANT CONNECT, RESOURCE TO harvest_user;
@/docker-entrypoint-initdb.d/create_harvest_table.sql
```

---

## API Endpoints

### 1. `POST /harvest`

Registers a new harvest record.

**Request Body** (`application/json`):

```json
{
  "area": 150.0,
  "production": 1800.0,
  "loss_percentage": 12.0,
  "duration_hours": 7.5,
  "harvest_method": "mechanical",
  "moisture_percentage": 25.0,
  "harvest_date": "2025-04-17",
  "operator_id": "OP12345",
  "equipment_id": "EQ67890",
  "variety": "RB867515",
  "ambient_temperature": 38.0,
  "brix_percentage": 10.0
}
```

| Field                | Type    | Description                                              |
|---------------------|---------|----------------------------------------------------------|
| `area`              | Float   | Harvest area in hectares (must be > 0).                  |
| `production`        | Float   | Gross yield in tons (≥ 0).                               |
| `loss_percentage`   | Float   | Estimated loss (%) [0–100], e.g., material drop.         |
| `duration_hours`    | Float   | Time spent in harvest (hours, > 0).                      |
| `harvest_method`    | String  | "manual" or "mechanical". Triggers method-specific rules.|
| `moisture_percentage`| Float  | Cane moisture (%) [0–100].                               |
| `harvest_date`      | String  | Date of harvest (YYYY‑MM‑DD).                            |
| `operator_id`       | String  | Identifier of the operator/team.                         |
| `equipment_id`      | String  | Identifier of the harvesting machine.                    |
| `variety`           | String  | Cane cultivar code (e.g., "RB867515").                   |
| `ambient_temperature`| Float | Ambient temperature (°C).                                |
| `brix_percentage`   | Float   | Sugar content (°Brix) [0–30].                            |

### Processing Steps

- **Validation**: Pydantic ensures type/range correctness.
- **Metrics**:
  - `lost_tonnage = production * (loss_percentage / 100)`
  - `net_production = production - lost_tonnage`
  - `productivity_per_hour = net_production / duration_hours`
  - `productivity_per_hectare = net_production / area`
- **Insights via `generate_advice`**:
  - Loss > 10%
  - Moisture > 20% (mechanical)
  - °Brix < 12
  - Low hourly productivity (< 200 t/h)
  - High temp & moisture (spoilage)
  - Operator losses > 15%, machine maintenance hints

- **Persistence**: Appended to `harvest_history.json`; inserted into Oracle.
- **Timestamp**: `created_at` set in “America/Sao_Paulo” timezone.

**Response (201 Created)**:

```json
{ "message": "Harvest created successfully" }
```

---

### 2. `GET /harvests`

Retrieves all harvest records, sorted by most recent.

**Response (200 OK)**:

```json
[
  {
    "id": 1,
    "area": 150,
    "production": 1800,
    "loss_percentage": 12,
    "lost_tonnage": 216,
    "net_production": 1584,
    "productivity_per_hour": 211.2,
    "productivity_per_hectare": 10.56,
    "alert": "Losses exceed the expected threshold (10%). High moisture level for mechanical harvesting. Low °Brix (10.0): sugar yield may be sub-optimal. High temp & moisture: risk of microbial spoilage.",
    "recommendation": "Check cutter bar pressure. Consider delaying harvest or using manual harvesting. Consider delaying harvest until Brix ≥ 12. Process cane quickly or lower moisture prior to storage.",
    "created_at": "2025-04-17T19:22:42"
  }
]
```

| Field                   | Description                                      |
|------------------------|--------------------------------------------------|
| `id`                   | Auto-generated record ID.                        |
| `lost_tonnage`         | Tonnes lost (abs.).                              |
| `net_production`       | Net yield (tons).                                |
| `productivity_per_hour`| Efficiency (t/h).                                |
| `productivity_per_hectare`| Efficiency (t/ha).                           |
| `alert`                | Concatenated alerts from business rules.         |
| `recommendation`       | Concatenated recommended actions.                |
| `created_at`           | Timestamp in ISO format (São Paulo time).        |

---

## Core Components & Subalgorithms

- **`models.py`** (Pydantic): schema + field validators.
- **`metrics.py`**: computes loss tonnage, net yield, hourly & per-ha productivity.
- **`advice.py`**: aggregates rule-based insights (loss thresholds, moisture, Brix, productivity, spoilage risk, operator/machine flags).
- **`storage.py`**: file I/O (JSON) for local audit trail.
- **`db.py`**: DB connection (`cx_Oracle`/`oracledb`), Oracle binding with Python-generated timestamp (`ZoneInfo`).

This structure demonstrates:

- **Subalgorithms**: modular functions with parameters.
- **Data structures**: dicts, lists, JSON files.
- **File manipulation**: reading/writing JSON.
- **DB connectivity**: Oracle schema, environment configs, SQL binding.

---

## Project Requirements & Validation

This implementation satisfies all initial requirements:

- **Área de Agronegócio**: foco na colheita de cana-de-açúcar e redução de perdas.
- **Subalgoritmos**: funções independentes para validação, cálculo e insights.
- **Estruturas de dados**: uso de listas para histórico, dicionários para payloads, tuplas internas para thresholds.
- **Manipulação de arquivos**: leitura e gravação de `harvest_history.json`.
- **Conexão Oracle**: persistência em banco de dados Oracle, com credenciais via variáveis de ambiente.
- **Clareza lógica**: fluxos POST → processing → persistence → GET.
- **Validação de entrada**: Pydantic assegura tipos e intervalos.
- **Documentação**: este README fornece contexto, uso e justificativas.

**All criteria outlined in the assignment have been implemented and validated.**

---

## License & Contribution

Contributions are welcome! Please open issues for bugs or feature requests, and submit PRs against the main branch. Ensure you maintain the integrity of the submission version post-deadline to avoid deduction.

© 2025 HarvestIQ Team
