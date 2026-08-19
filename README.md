# Sports Injury Risk Detection System

An AI-based sports injury risk detection system that allows athletes to create profiles, upload sports videos, and analyze movement data to identify potential injury risks.

## 🚀 Live Deployment

Frontend:

[clickable Text Here](https://sports-injury-risk-detection-deployment-1.onrender.com)

Backend API:

https://sports-injury-risk-detection-deployment.onrender.com/

## ✅ What Has Been Implemented

### Authentication
- User registration and login
- JWT-based authentication
- Password hashing and verification
- Google authentication
- Role-based user system
- Persistent user sessions

### Athlete Profile
- Athlete profile creation
- Sport and position information
- Age, height and weight
- Training load
- Flexibility
- Strength
- Balance
- Endurance
- Coach notes

### Video Management
- Upload sports videos
- Supported formats:
  - MP4
  - MOV
  - AVI
  - MKV
- Automatic video metadata extraction
- Duration detection
- FPS detection
- Resolution detection
- Video storage and retrieval
- Athlete-specific video listing
- Video playback

### Database
- PostgreSQL database
- User management
- Athlete profiles
- Video records
- Injury history
- Relationships between users, athletes and videos

### Backend API
- FastAPI backend
- REST API endpoints
- JWT authentication
- CORS configuration
- PostgreSQL integration
- Static file/video serving
- Video metadata processing

### Frontend
- React + Vite
- Authentication pages
- Dashboard
- Athlete profile
- Video upload
- My Videos section
- Protected routes
- API integration with backend

## 🧠 Video Processing

When a video is uploaded:

1. The video is validated.
2. A unique filename is generated.
3. The video is stored.
4. Video metadata is extracted.
5. Video information is stored in PostgreSQL.
6. The uploaded video can be viewed from the My Videos section.

## 🗄️ Database

The application uses PostgreSQL with the following major entities:

- Users
- Athletes
- Videos
- Injury History

Users and athlete profiles are connected using user IDs, while uploaded videos are associated with the corresponding athlete.

## 💻 Run Locally

### 1. Clone the Repository

```bash
git clone <your-github-repository-url>
cd sports-injury-risk-detection

## Backend

Go to the backend directory:

```bash
cd backend