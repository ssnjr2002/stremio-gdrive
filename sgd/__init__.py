import os
import json
from flask import Flask
from sgd.gdrive import GoogleDrive

app = Flask(__name__)
token = "{"token": "ya29.a0AX9GBdUzIrVmhY1JnJac1D47l9nAeZ8sWNUZ-a8qLRIanL2_mPdmEPt6eBZANzsgUVc5DhjeO6rRz4pb5wb8z80QsNQaCOtXt6WaodafYPa83XdiX6STTVC_0gYjgTQt98BjAH5nCG9jC_3pVbTFoAjUntpOaCgYKAaUSARESFQHUCsbCbDgZ0EVPk1GynZmTX-RHEg0163", "refresh_token": "1//0egylBAfj8chmCgYIARAAGA4SNwF-L9IrnDTQQJswYcld8xm9_VpXsRfADcd3cyZpA4YC0Ls4RWyFkA7kh6dbHLUFgLopgeTJLqU", "token_uri": "https://oauth2.googleapis.com/token", "client_id": "202264815644.apps.googleusercontent.com", "client_secret": "X4Z3ca8xfWDb1Voo-F9a7ZxJ", "scopes": ["https://www.googleapis.com/auth/drive"]}"
gdrive = GoogleDrive(token)

from sgd import routes
