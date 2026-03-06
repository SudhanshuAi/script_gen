# How to Run Data Forge Platform

This guide will help you set up and run the Data Forge Platform locally.

## Prerequisites

- **Python 3.12+**
- **Node.js 18+** (with npm)
- **PostgreSQL** (Optional, only if you want to push data directly to a database)

---

## 1. Backend Setup

The backend handles data generation and provides the API.

1. **Navigate to the backend directory**:
   ```powershell
   cd backend
   ```

2. **Create a virtual environment**:
   ```powershell
   python -m venv .venv
   ```

3. **Activate the virtual environment**:
   - **Windows**: `.\.venv\Scripts\activate`
   - **macOS/Linux**: `source .venv/bin/activate`

4. **Install dependencies**:
   ```powershell
   pip install -r requirements.txt
   ```

5. **Run the server**:
   ```powershell
   uvicorn main:app --reload --port 8000
   ```
   *The backend will now be running at `http://localhost:8000`.*

---

## 2. Frontend Setup

The frontend provides the interactive dashboard.

1. **Navigate to the frontend directory**:
   ```powershell
   cd frontend
   ```

2. **Install dependencies**:
   ```powershell
   npm install
   ```

3. **Run the development server**:
   ```powershell
   npm run dev
   ```
   *The frontend will now be running at `http://localhost:5173`.*

---

## 3. Basic Usage

1. Open your browser to `http://localhost:5173`.
2. You will see a sample YAML schema in the editor.
3. (Optional) Configure your Database in **DB Settings** if you want to export to Postgres.
4. Click **Validate** to check your schema.
5. Click **Mock Me** to start the generation.
6. Once finished, download your generated data files or browse the mock API dumps directly from the dashboard results.

## Troubleshooting

- **CORS Issues**: Ensure the backend is running on port 8000. The frontend is configured to look for the API at `http://localhost:8000`.
- **Database Connection**: If using a remote DB (like Neon), ensure you append `?sslmode=require` to your connection string.
- **Python Version**: Ensure you are using Python 3.12 or newer, as some libraries used for data handling require recent versions.
