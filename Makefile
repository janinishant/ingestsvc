.PHONY: dev build build-frontend check format clean help tail-log

# Default target
help:
	@echo "Available targets:"
	@echo "  dev       - Start development servers (frontend + backend)"
	@echo "  build     - Build production binary with embedded frontend"
	@echo "  check     - Run linting and type checking"
	@echo "  format    - Format all code"
	@echo "  clean     - Clean build artifacts"
	@echo "  tail-log  - Show the last 100 lines of the log"

# Development mode - start both frontend and backend
dev:
	@ENV=development ./scripts/shoreman.sh Procfile


tail-log:
	@tail -100 ./dev.log | perl -pe 's/\e\[[0-9;]*m(?:\e\[K)?//g'