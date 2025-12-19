# RuneScape Lite Advisor

A local web application that provides personalized next-step advice for RuneScape players based on their profile (stats, goals, game mode).

## Tech Stack

- **Frontend**: Vite + React + TypeScript
- **Backend**: Python FastAPI
- **Database**: SQLite (stored in Docker volume)
- **Development**: Docker Compose with hot reload

## Quick Start

### Prerequisites

- Docker and Docker Compose installed
- Ports 8000 and 5173 available

### Build and Run

```bash
docker compose up --build
```

This will:
- Build and start the backend API on port 8000
- Build and start the frontend on port 5173
- Initialize the SQLite database in a Docker volume

### Access the Application

- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

### Stop the Application

```bash
docker compose down
```

### Reset the Database

To completely wipe the database and start fresh:

```bash
# Stop containers
docker compose down

# Remove the database volume
docker volume rm rs-lite-advisor_db_data

# Start again (will create fresh database)
docker compose up --build
```

Alternatively, you can remove all volumes:

```bash
docker compose down -v
```

## Project Structure

```
rs-lite-advisor/
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── main.py           # FastAPI application
│   ├── models.py         # Pydantic models
│   ├── database.py       # Database access layer
│   └── advisor_engine.py # Rule-based advisor logic
├── frontend/
│   ├── Dockerfile
│   ├── package.json
│   ├── vite.config.ts
│   ├── index.html
│   └── src/
│       ├── main.tsx
│       ├── App.tsx
│       ├── App.css
│       └── index.css
├── docker-compose.yml
├── README.md
└── .gitignore
```

## Features

### Profile Management
- Game mode selection (Main, Ironman, Hardcore Ironman, Group Ironman)
- Membership status (F2P/P2P)
- Goals selection (questing, combat, skilling, gp, diaries)
- Playtime tracking
- Skills editor with default skills and custom skill support

### Advice Engine
- Rule-based recommendation system
- Returns exactly 3 personalized recommendations
- Each recommendation includes:
  - Title
  - "Why now" rationale
  - Step-by-step action items

### API Endpoints

- `GET /health` - Health check
- `GET /profile` - Get current profile (creates default if none exists)
- `PUT /profile` - Update profile
- `POST /advice` - Get advice based on current profile

## Development

### Hot Reload

Both services support hot reload:
- Backend: Changes to Python files automatically restart the server
- Frontend: Changes to React/TypeScript files automatically refresh the browser

### Database Location

The SQLite database is stored at `/data/app.db` inside the Docker volume `db_data`. This persists between container restarts.

## Notes

- The application stores a single profile (MVP assumption)
- The advisor engine uses simple rule-based logic based on membership, goals, and skill levels
- All recommendations are deterministic based on the current profile state

