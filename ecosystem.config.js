module.exports = {
  apps: [
    {
      name: "papermind-api",
      cwd: "./backend",
      script: ".venv/bin/uvicorn",
      args: "main_api:app --host 0.0.0.0 --port 8000",
      interpreter: "none",
      env: {
        QDRANT_URL: "http://localhost:6333",
      },
    },
    {
      name: "papermind-ingestion",
      cwd: "./backend",
      script: ".venv/bin/flask",
      args: "--app main_ingestion run --host 0.0.0.0 --port 5001",
      interpreter: "none",
      env: {
        QDRANT_URL: "http://localhost:6333",
      },
    },
    {
      name: "papermind-frontend",
      cwd: "./frontend",
      script: "npm",
      args: "start",
      env: {
        NEXT_PUBLIC_API_URL: "http://localhost:8000",
        PORT: "3000",
      },
    },
  ],
};
