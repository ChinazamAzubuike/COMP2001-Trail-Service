# COMP2001-Trail-Service
COMP2001 CW2


**Overview**
The Trail Management Service is a Flask-based RESTful API that allows users to manage trails, including creating, updating, and retrieving trail information. The service includes role-based authorisation, token-based authentication using JWT, and integrates Swagger documentation for easy API exploration.

**Features**
•	User Authentication: Log in as a user or admin using JWT.
•	Role-Based Access Control: 
 -	Admins can create, update, and delete trails.
 -	Users can view trails.
•	CRUD Operations for Trails: 
 - Create new trails.
 - Retrieve trail details by ID.
 - Update and delete trails (admin only).
•	Trail Features Management: Update trails.
•	Swagger Integration: API documentation available at /apidoc/ (http://127.0.0.1:5000/apidoc/).
•	Dockerised Deployment: Easily build and run the application in a Docker container.

**Technologies Used**
•	Backend: Flask
•	Database: Azure Data Studio
•	Authentication: JSON Web Token (JWT)
•	API Documentation: Flasgger (Swagger UI)
•	Deployment: Docker

**Prerequisites**
1.	Python 3.8
2.	Docker
3.	Microsoft SQL Server.

**Installation**
**1.** Clone the Repository
git clone https://github.com/ChinazamAzubuike/COMP2001-Trail-Service.git
cd trail-management-service
**2.** Set Up Environment
Install dependencies: pip install -r requirements.txt
**3.** Configure Database
Update the pyodbc.connect line in app.py with your database credentials: 
1.	conn = pyodbc.connect(
2.	    'DRIVER={ODBC Driver 17 for SQL Server};'
3.	    'SERVER=your-server-name;'
4.	    'DATABASE=your-database-name;'
5.	    'UID=your-username;'
6.	    'PWD=your-password;'
7.	)
**4.** Run the Application
python app.py
Access the API at: http://127.0.0.1:5000/

**Docker Deployment**
**1**. Build the Docker Image
docker build -t trail-service .
**2.** Run the Docker Container
docker run -p 8000:5000 trail-service
Access the API at: http://127.0.0.1:8000/

**API Endpoints**
•Authentication:
 - POST /login: Login and retrieve a JWT token.
   •Trails
 - POST /trails: Create a new trail (Admin only).
 - GET /trails: Retrieve all trails.
 - GET /trails/<trail_id>: Retrieve a specific trail by ID.
 - PUT /trails/<trail_id>: Update a trail (Admin only).
 - DELETE /trails/<trail_id>: Delete a trail (Admin only).
   •Users
 - POST /users: Create a new user.
 - GET /users: Retrieve all users.
 - GET /users/<user_id>: Retrieve a specific user by ID.

**Swagger Documentation**
Access Swagger UI at:
http://127.0.0.1:5000/apidoc/

**Troubleshooting**
Common Issues:
1.	Database Connection Errors:
-	Ensure the database credentials are correct.
-	Verify that the database server is running and accessible.
2.	Token Missing/Invalid:
-	Include the Authorisation header in the format: Bearer <token>.
3.	Features Not Displaying:
-	Ensure the CW2.Trail_Feature_Map table is populated correctly.



Author
Chinazam Azubuike
