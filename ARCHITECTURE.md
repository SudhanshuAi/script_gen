# Data Forge Platform - Architecture Overview

Data Forge Platform is a high-performance, schema-driven mock data generation engine. It allows users to define complex data structures via YAML and generate millions of rows across multiple output formats.

## System Components

### 1. Frontend (React + Vite)
- **Role**: User Interface and Orchestration.
- **Key Features**:
    - **YAML Editor**: Powered by CodeMirror with syntax highlighting for schema definition.
    - **Validation Engine**: Communicates with the backend to ensure schemas are logically sound before generation.
    - **Status Monitoring**: Polls the backend asynchronously to track long-running data generation jobs.
    - **Results Dashboard**: Displays execution metrics and provides download links for generated artifacts.

### 2. Backend (FastAPI + Python)
- **Role**: Core Logic, Job Management, and Data Engineering.
- **Key Features**:
    - **FastAPI Core**: Handles RESTful requests for validation, job submission, and status tracking.
    - **Job Manager**: Manages an asynchronous background queue to prevent blocking the API during massive data generations.
    - **Schema Adapter & Validator**: Normalizes user-defined YAML and verifies data types, constraints, and relationships.
    - **Data Generator**: Utilizes **Faker** for realistic value generation and **Pandas/PyArrow** for high-efficiency data handling and chunking.
    - **Database Manager**: Handles optimized bulk loading into PostgreSQL using the `copy_from` protocol.

## Data Flow

1. **Schema Definition**: User writes a YAML schema in the frontend.
2. **Validation**: Frontend sends the schema to `/validate`. Backend checks for syntax errors, circular dependencies, and invalid types.
3. **Job Submission**: User clicks "Mock Me". Frontend sends schema and connection settings to `/generate`.
4. **Asynchronous Generation**:
    - Backend creates a `job_id` and starts a background thread.
    - Entities are sorted topologically to respect Foreign Key constraints.
    - Data is generated in chunks to remain memory-efficient.
    - Data is streamed to files (CSV, Parquet, JSON, Excel) and/or piped into PostgreSQL.
5. **Monitoring**: Frontend polls `/status/{job_id}` until completion.
6. **Delivery**: Upon completion, the backend provides URIs to download files or browse paginated JSON API dumps.

## Technology Stack
- **Frontend**: React, Vite, Tailwind CSS, Lucide React, Framer Motion, CodeMirror.
- **Backend**: Python 3.12+, FastAPI, Uvicorn, Pandas, PyArrow, Psycopg2, SQLAlchemy, Faker.
- **Storage**: PostgreSQL (optional sink), Local filesystem for file artifacts.
