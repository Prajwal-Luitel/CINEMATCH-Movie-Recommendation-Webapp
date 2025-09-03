# Webapp Setup

First follow the manual for this repo readme:-
```sh
https://github.com/Prajwal-Luitel/Movie-Recommendation-ETL
```

## How to use

### 1. Clone the repo

```sh
git clone https://github.com/Prajwal-Luitel/CINEMATCH-Movie-Recommendation-Webapp Cinematch
cd Cinematch
```
### 2. Activate Virtual Environment (used in etl)

#### Activate on Linux/Mac
source venv/bin/activate

#### Activate on Windows (PowerShell)
venv\Scripts\activate

#### Activate on Windows (CMD)
venv\Scripts\activate.bat

### 3. Install django

- pip install django

### 4. Initialize Django Backend
```sh
PG_UN=postgres PG_PW=postgres python manage.py migrate

PG_UN=postgres PG_PW=postgres python manage.py makemigrations

PG_UN=postgres PG_PW=postgres python manage.py runserver
```

- Access the Application
Open your browser and navigate to:
http://127.0.0.1:8000/