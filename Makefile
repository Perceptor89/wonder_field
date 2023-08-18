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
	sudo docker-compose up --build -d
	sudo docker exec -d -it backend python -m celery -A django_app worker -l info
	sudo docker exec -d -it backend python manage.py poller_start

project-stop:
	sudo docker-compose down

server:
	ssh perceptor@185.250.205.16
