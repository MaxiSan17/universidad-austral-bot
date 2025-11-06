.PHONY: help install run test clean docker-up docker-down

help:
	@echo "Comandos disponibles:"
	@echo "  make install    - Instalar dependencias"
	@echo "  make run        - Ejecutar aplicación localmente"
	@echo "  make test       - Ejecutar tests"
	@echo "  make docker-up  - Levantar servicios con Docker"
	@echo "  make docker-down - Bajar servicios Docker"
	@echo "  make clean      - Limpiar archivos temporales"

install:
	pip install -r requirements.txt

run:
	python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

test:
	pytest tests/ -v

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

logs:
	docker-compose logs -f university-agent