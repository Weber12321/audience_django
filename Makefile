PORT=8080

run_server:
	@eval "python manage.py runserver $(PORT)"
run_shell:
	@eval "python manage.py shell"
