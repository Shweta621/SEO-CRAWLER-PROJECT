from flask_sqlalchemy import SQLAlchemy
db = SQLAlchemy()


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(30),nullable=False,unique=True)
    name = db.Column(db.String(25), nullable=False)
    password = db.Column(db.String(16), nullable=False)
    cpass = db.Column(db.String(16), nullable=False)
    def __init__(self,email,name,password,cpass):
        self.email = email
        self.name = name
        self.password = password
        self.cpass = cpass
    def check_password(self, password):
        return self.password== password
   

def creatuser(email,name,password,cpass):
    user = User(email=email,name=name,password=password,cpass=cpass)            # Create a data with the provided input
    db.session.add(user)        # Actually add data to the database
    db.session.commit()      # Save all pending changes to the database
    return user