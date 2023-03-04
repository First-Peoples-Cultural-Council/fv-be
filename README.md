This branch contains a simple example shared database implementation using Django-Guardian for permissions

### Setup:

#### Install dependencies:
```
pip install -r requirements.txt
```

#### Setup database:
```
python manage.py makemigrations app
python manage.py migrate
```

#### Setup an admin account:
```
python manage.py createsuperuser
```

#### Start the server:
```
python manage.py runserver
```

### Usage:
Admin page: ```localhost:8000/admin/```  
Main REST API page: ```localhost:8000/```  
Languages endpoint: ```localhost:8000/languages/```  
Words endpoint for a language: ```localhost:8000/<language UUID>/words/```  
Phrases endpoint for a language: ```localhost:8000/<language UUID>/phrases/``` 
