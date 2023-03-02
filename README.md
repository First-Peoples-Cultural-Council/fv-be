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

#### Add public group permission to the default anonymous user
Login to the admin page at ```localhost:8000/admin/```, navigate to the users page at 
```http://localhost:8000/admin/auth/user/```, click on the ```AnonymousUser```, add the public group to the user's 
chosen groups and hit save. 

### Usage:
Admin page: ```localhost:8000/admin/```  
Main REST API page: ```localhost:8000/```  
Languages endpoint: ```localhost:8000/languages/```  
Words endpoint for a language: ```localhost:8000/<language UUID>/words/```  
Phrases endpoint for a language: ```localhost:8000/<language UUID>/phrases/``` 