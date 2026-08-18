# sports-injury-risk-detection
Project Overview

The system is being developed to analyze sports/athlete videos and identify movement patterns that may indicate an increased risk of injury.

The current backend provides:

User authentication
Athlete profile management
Video upload
Video metadata extraction
Video storage
Pose detection infrastructure
Pose landmark extraction
Joint angle calculation infrastructure
Video processing infrastructure
PostgreSQL database integration

The project is currently under development. Risk prediction and advanced analysis will be integrated in the next stages.

Installation
1. Clone the Repository
git clone <repository-url>
cd sports-injury-risk-detection
2. Create Python Virtual Environment
cd backend

python -m venv myvenv
Windows
myvenv\Scripts\activate
3. Install Backend Dependencies
pip install -r requirements.txt
4. Configure Environment Variables

Create a .env file inside the backend directory.

Example:

DATABASE_URL=postgresql://username:password@localhost:5432/database_name
SECRET_KEY=your_secret_key
ALGORITHM=HS256

Do not commit .env to GitHub.

Running the Backend

From the backend directory:

uvicorn app.main:app --reload

The API will run on:

http://127.0.0.1:8000

FastAPI documentation:

http://127.0.0.1:8000/docs
Running the Frontend

From the frontend directory:

npm install
npm run dev

The frontend will normally run on:

http://localhost:5173
Python Requirements

The backend currently depends on packages including:

fastapi
uvicorn
sqlalchemy
psycopg2-binary
python-dotenv
python-jose
passlib
bcrypt
pydantic
opencv-python
mediapipe
python-multipart

The exact versions should be maintained in:

backend/requirements.txt