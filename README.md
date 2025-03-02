# Groupme Meme Bot
A toy project to build a bot for groupme with a flask-python backend.

## Requirements 📋
- Python 3.8+
- PostgreSQL

## Setup 🛠️
1. Install uv (follow instructions [here](https://docs.astral.sh/uv/#getting-started))

2. Clone the repository:
```bash
git clone https://github.com/yourusername/minimalistic-fastapi-template.git
cd minimalistic-fastapi-template
```

3. Install dependencies with uv:
```bash
uv sync
```

4. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your database credentials
```

### Old Readme

### Runing Locally:
1. Have Python 3.7 and pip installed locally (I reccoemnd using a [virtual environment](https://packaging.python.org/guides/installing-using-pip-and-virtual-environments/))
2. run ```pip -r requirements.txt```
3. run ```python main.py```
4. alternatively, you can use ```heroku local -f Procfile.windows```

### Deploying:
I deployed using [Heroku](https://dashboard.heroku.com/), but you could probably container service you like. 

1. Creat a Heroku project
2. Go to the project settings, and ```reveal config vars```
3. Scroll down and add the ```heroku/python buildpack```
4. Add two items:
   1. API_TOKEN, the key for which should be your Groupme Application API Token from [here](https://dev.groupme.com/applications) - Click the application you'd like to access and copy your ```access token```
   2. Bot ID from [here](https://dev.groupme.com/bots)
5. Follow the instructions at ```https://dashboard.heroku.com/apps/<Your App Name>/deploy/heroku-git``` to deploy
6. Profit

## Reference:
Some useful links.
* [Creating and using a python virtual environment](https://packaging.python.org/guides/installing-using-pip-and-virtual-environments/)
* [Making a simple flask webserver](https://www.freecodecamp.org/news/how-to-build-a-web-application-using-flask-and-deploy-it-to-the-cloud-3551c985e492/)
* [Groupme bot API](https://dev.groupme.com/tutorials/bots)
* [Groupme bot Docs](https://dev.groupme.com/docs/v3)
* [Python Groupme API wrapper](https://github.com/rhgrant10/Groupy)
* [Python Groupme API Docs](https://groupy.readthedocs.io/en/latest/pages/quickstart.html)
* [How to add a react front end (if desired)](https://blog.miguelgrinberg.com/post/how-to-create-a-react--flask-project)
* [Library for Async Processing (Celery)](https://docs.celeryproject.org/en/latest/index.html)
* [Fuzzy string matching (fuzzywuzzy)](https://www.datacamp.com/community/tutorials/fuzzy-string-python)