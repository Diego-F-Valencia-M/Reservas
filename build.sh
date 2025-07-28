#!/usr/bin/env bash

# Instala las dependencias
pip install -r requirements.txt

# Recolecta archivos estáticos
python manage.py collectstatic --noinput

# Ejecuta migraciones
python manage.py migrate