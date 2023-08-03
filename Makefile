poller-start:
	python manage.py poller_start

migrate:
	python manage.py makemigrations
	python manage.py migrate

django-start:
	python manage.py runserver

celery-start:
	python -m celery -A django_app worker -l info

project-run:
	docker-compose up --build -d
	docker exec -d -it backend python -m celery -A django_app worker -l info
	docker exec -d -it backend python manage.py poller_start

project-stop:
	docker-compose down