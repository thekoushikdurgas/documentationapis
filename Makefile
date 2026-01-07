.PHONY: install run test lint format clean docker-build docker-run docker-up docker-down sam-build sam-deploy sam-validate sam-local sam-logs sam-delete validate test-local

# Install dependencies
install:
	pip install -r requirements.txt

# Run the application locally
run:
	uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload

# Run tests
test:
	pytest tests/ -v

# Lint code
lint:
	ruff check app/ tests/
	mypy app/

# Format code
format:
	ruff format app/ tests/
	black app/ tests/

# Clean build artifacts
clean:
	find . -type d -name "__pycache__" -exec rm -r {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.pyd" -delete
	find . -type d -name "*.egg-info" -exec rm -r {} +
	find . -type d -name ".pytest_cache" -exec rm -r {} +
	find . -type d -name ".mypy_cache" -exec rm -r {} +

# Build Docker image
docker-build:
	docker build -t documentation-api:latest .

# Run Docker container
docker-run:
	docker run -p 8080:8080 --env-file .env documentation-api:latest

# Start docker-compose
docker-up:
	docker-compose up -d

# Stop docker-compose
docker-down:
	docker-compose down

# View logs
docker-logs:
	docker-compose logs -f documentation-api

# SAM Commands
sam-build:
	sam build --use-container --no-cache

sam-build-clean:
	rm -rf .aws-sam
	sam build --use-container --no-cache

sam-deploy:
	sam deploy

sam-deploy-guided:
	sam deploy --guided

sam-validate:
	sam validate --lint

sam-local:
	sam local start-api --port 3000 --host 0.0.0.0

sam-logs:
	sam logs -n DocumentationApiFunction --stack-name documentation-api-stack --tail

sam-delete:
	sam delete --stack-name documentation-api-stack

# Validation and Testing
validate:
	python scripts/validate_setup.py

test-local:
	python scripts/test_local.py

verify-deployment:
	python scripts/verify_deployment.py
