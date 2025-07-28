#!/usr/bin/env bash

# Instala las dependencias
pip install -r requirements.txt

# Ejecuta migraciones
python manage.py migrate

# Recolecta archivos estáticos
python manage.py collectstatic --noinput