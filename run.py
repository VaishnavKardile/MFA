from app import create_app
from dotenv import load_dotenv
load_dotenv()

app = create_app()

if __name__ == '__main__':
    # debug=True means the server will automatically restart when you save changes!
    app.run(debug=True)