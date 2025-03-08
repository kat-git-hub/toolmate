install:
	poetry install
lint:
	poetry run flake8 app --ignore=E501
runserver:
	poetry run python run.py
migrate:
	poetry run python app.py migrate
migrations:
	poetry run python app.py makemigrations
test:
	poetry run pytest -vv
test-coverage:
	poetry run pytest --cov=app --cov-report xml