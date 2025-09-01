# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

ingestsvc is a python service exposing endpoints to securely ingest raw logs from fluent-bit log collector.

## Development Commands

```bash
make dev          # Development (starts both frontend and backend.  This autoreloads and auto compiles.  Don't ever stop the server)
make build        # Production build (we rarely need this)
make check        # Linting and type checking (for backend and frontend)
make format       # Code formatting (for backend and frontend)
make clean        # Clean build artifacts (we rarely need this)
make tail-log     # Reads the current log file (last 100 lines of code)
```

**IMPORTANT:**

* The server and the frontend log everything into the dev.log file.
* Use the `make tail-log` command to read the log file. 
* The schema for storing the *
* If you fail to run the Makefile, you have to remember that you have to run it from the top-level directory.

## Architecture

**Backend (Go)**
- Single binary using Chi router with standard HTTP stack
- Postgres database schema in directory `pg_schemas/schemas/dev_demo`


**Development Setup**
- Uses Procfile with custom shoreman.sh script
- Frontend dev server proxies `/api` requests to backend
- Watchexec for auto-reloading Go backend on file changes

## Database Schema

- Schema for postgres is in `pg_schemas/schemas/dev_demo` maintained as different migrations on the database.

## Development Notes

- Backend runs on port 8080 by default
- Environment variable PORT can override default port
- Always use test driven development approach