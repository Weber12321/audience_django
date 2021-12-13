LOCALHOST=127.0.0.1
REMOTE_HOST=0.0.0.0
PORT=8080

run_server_local:
	@eval "python manage.py runserver $(LOCALHOST):$(PORT)"
run_server_remote:
	@eval "python manage.py runserver $(REMOTE_HOST):$(PORT)"
run_shell:
	@eval "python manage.py shell"
