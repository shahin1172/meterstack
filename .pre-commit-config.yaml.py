repos:
  - repo: https://github.com/psf/black
    rev: 23.12.1
    hooks:
      - id: black
        language_version: python3.12
  - repo: https://github.com/pycqa/flake8
    rev: 7.0.0
    hooks:
      - id: flake8
        args: ['--max-line-length', '120', '--extend-ignore', 'E203,W503']
  - repo: local
    hooks:
      - id: django-tests
        name: Run Django tests
        entry: python manage.py test --noinput
        language: system
        pass_filenames: false
        types: [python]