# 651-Web-G6
651 Project

1. get location when posting
2. show map and markers in the profile
3. change 'search' into 'search user' or 'search post(location, caption)'
4. change database 'MySQL' to 'PostgreSQL'
5. visit at https://35.183.67.139


# Start env
Start manually:
```
pg_ctl -D /usr/local/var/postgres start
```

Stop manually:
```
pg_ctl -D /usr/local/var/postgres stop
```

# Start Development Server

```
python manage.py runserver
```

# Deployment

```
pip install -r requirements.txt
python manage.py makemigrations
python manage.py migrate
python manage.py collectstatic
```

