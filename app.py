from config import app, db
from routes import main

app.register_blueprint(main)

if __name__ == '__main__':
    db.create_all()  # Create tables if not already present
    app.run(debug=True)