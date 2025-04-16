from models.models import db
import os

#def init_db(app):
    #with app.app_context():
        #db.create_all()

import os

def init_db(app):
    db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace("sqlite:///", "")
    if not os.path.exists(db_path):
        with app.app_context():
            print("Luodaan uusi tietokanta:", db_path)
            db.create_all()
    else:
        print("Tietokanta jo olemassa, ei luoda uudelleen:", db_path)