# Udacity Project 4: Item Catalog

## Prerequisites
- Flask
- Sqlite
- Python 2.7
*This app was build with python 2.7, it may not work with python 3*

## Local Deployment Instruction
1. Download or clone this repository
2. In the terminal, navigate to the root folder (where `project.py` is located)
3. Create `instance` folder in the root folder.
4. Inside `instance`, create `config.py` with your configurations.
5. Setup database using `python database_setup.py`
6. Populate database using `python populator.py`
7. Start the app using `python project.py`
8. The app should now be running at `http://localhost:5000`

## Sample `config.py`

```python
import os

# grab the folder of the top-level directory of this project
BASEDIR = os.path.abspath(os.path.dirname(__file__))
TOP_LEVEL_DIR = os.path.abspath(os.curdir)

SECRET_KEY = 'super_secret_key'
DEBUG = True
CLIENT_ID = 'YOUR_CLIENT_ID_FROM_GOOGLE'
```