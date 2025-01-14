from flask import Flask, jsonify, request
from flasgger import Swagger

from functools import wraps
import jwt
import datetime

import pyodbc

# Database connection
conn = pyodbc.connect(
    'DRIVER={ODBC Driver 17 for SQL Server};'
    'SERVER=DIST-6-505.uopnet.plymouth.ac.uk;'
    'DATABASE=COMP2001_CAzubuike;'
    'UID=CAzubuike;'
    'PWD=JftB154*;'
)
cursor = conn.cursor()

app = Flask(__name__)

#swagger = Swagger(app)

trails = []

swagger_config = {
    "headers": [],
    "specs": [
        {
            "endpoint": 'apispec',
            "route": '/apispec.json',
            "rule_filter": lambda rule: True,
            "model_filter": lambda tag: True,
        }
    ],
    "static_url_path": "/flasgger_static",
    "swagger_ui": True,
    "specs_route": "/apidoc/",  # Ensure this matches your intended route
    "securityDefinitions": {
        "Bearer": {
            "type": "apiKey",
            "name": "Authorization",
            "in": "header",
            "description": "Enter 'Bearer <token>' to authenticate.",
        }
    },
    "security": [{"Bearer": []}],
}

swagger = Swagger(app, config=swagger_config)


SECRET_KEY = 'admins_only_pass_key'


def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'error': 'Token is missing'}), 401  # Stop here if no token is provided

        try:
            # Decode the token
            data = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token has expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Invalid token'}), 401

        # Pass the decoded token data to the endpoint
        return f(data, *args, **kwargs)

    return decorated


def admin_required(f):
    @wraps(f)
    def decorated(data, *args, **kwargs):
        if data.get('role') != 'admin':  # Check if the user's role is admin
            return jsonify({'error': 'Admin access required'}), 403  # Stop for non-admin users
        return f(data, *args, **kwargs)

    return decorated


# CREATE a new trail
@app.route('/trails', methods=['POST'])
@token_required
@admin_required
def create_trail():
    """
    Admins can create a new trail
    ---
    tags:
      - Trails
    parameters:
      - in: header
        name: Authorization
        required: true
        type: string
        description: "Bearer <JWT Token>"
      - in: body
        name: body
        schema:
          type: object
          required:
            - name
            - difficulty
            - length
            - location
          properties:
            name:
              type: string
              example: "River Walk"
            difficulty:
              type: string
              example: "Easy"
            length:
              type: number
              example: 4.2
            location:
              type: string
              example: "Cornwall, UK"
            elevation_gain:
              type: number
              example: 200
            route_id:
              type: integer
              example: 1
            summary:
              type: string
              example: "A lovely riverside walk."
            description:
              type: string
              example: "Perfect for families."
            features:
              type: array
              items:
                type: string
                example: "Historic Sites"
    responses:
      201:
        description: Trail created successfully
      400:
        description: Invalid input
      500:
        description: Internal Server Error
    """
    try:
        data = request.json

        # Step 1: Insert the trail
        cursor.execute(
            """
            INSERT INTO CW2.Trails (name, difficulty, length, location, elevation_gain, route_id, summary, description)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            data['name'], data['difficulty'], data['length'], data['location'],
            data.get('elevation_gain'), data.get('route_id'), data.get('summary'), data.get('description')
        )
        conn.commit()

        # Step 2: Get the generated trail_id
        cursor.execute("SELECT SCOPE_IDENTITY()")
        trail_id_row = cursor.fetchone()
        if not trail_id_row or trail_id_row[0] is None:
            raise Exception("Failed to retrieve the new Trail ID.")

        trail_id = trail_id_row[0]

        # Step 3: Handle features
        for feature in data.get('features', []):
            cursor.execute("SELECT feature_id FROM CW2.Features WHERE feature_name = ?", feature)
            feature_row = cursor.fetchone()
            if not feature_row:
                # Insert the feature if it doesn't exist
                cursor.execute("INSERT INTO CW2.Features (feature_name) VALUES (?)", feature)
                conn.commit()
                cursor.execute("SELECT feature_id FROM CW2.Features WHERE feature_name = ?", feature)
                feature_row = cursor.fetchone()
            feature_id = feature_row[0]

            # Insert the mapping into Trail_Feature_Map
            cursor.execute("INSERT INTO CW2.Trail_Feature_Map (trail_id, feature_id) VALUES (?, ?)", trail_id, feature_id)
            conn.commit()

        return jsonify({'message': 'Trail created successfully', 'trail_id': trail_id}), 201

    except Exception as e:
        return jsonify({'error': str(e)}), 500





@app.route('/login', methods=['POST'])
def login():
    """
    Login a user and generate a JWT access token
    ---
    tags:
      - Users
    parameters:
      - in: body
        name: body
        schema:
          type: object
          required:
            - email
            - password
          properties:
            email:
              type: string
              example: "tim@plymouth.ac.uk"
            password:
              type: string
              example: "COMP2001!"
    responses:
      200:
        description: Login successful
      401:
        description: Invalid email or password
    """
    data = request.json
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({'error': 'Email and password are required'}), 400

    # Query the database for the user
    cursor.execute("SELECT UserID, Role, Password FROM CW2.Users WHERE Email = ?", email)
    row = cursor.fetchone()

    # Check if the user exists and the password matches
    if row and row[2] == password:
        # Generate JWT token
        token = jwt.encode(
            {
                'user_id': row[0],
                'role': row[1],
                'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=1)
            },
            SECRET_KEY,
            algorithm='HS256'
        )
        return jsonify({'access_token': token}), 200
    else:
        return jsonify({'error': 'Invalid email or password'}), 401







# GET a trail by id
@app.route('/trails/<int:trail_id>', methods=['GET'])
def get_trail_by_id(trail_id):
    """
    Get trail by ID
    Fetch details of a specific trail by its ID, including route and features.
    ---
    tags:
      - Trails
    parameters:
      - in: path
        name: trail_id
        required: true
        type: integer
        description: The ID of the trail to fetch
    responses:
      200:
        description: Details of the trail
        schema:
          type: object
          properties:
            TrailID:
              type: integer
              example: 1
            Name:
              type: string
              example: "Plymbridge Circular"
            Difficulty:
              type: string
              example: "Easy"
            Length:
              type: number
              example: 4.5
            Location:
              type: string
              example: "Plymouth, Devon"
            ElevationGain:
              type: number
              example: 120
            Summary:
              type: string
              example: "A scenic trail through woodland."
            Description:
              type: string
              example: "Explore the beautiful woods along the Plymbridge."
            RouteType:
              type: string
              example: "Loop"
            Features:
              type: array
              items:
                type: string
                example: "Historic Sites"
      404:
        description: Trail not found
    """
    cursor.execute("""
        SELECT t.Trail_ID, t.name, t.difficulty, t.length, t.location, t.elevation_gain, t.summary, t.description, rt.route_name
        FROM CW2.Trails t
        JOIN CW2.Route_Types rt ON t.route_id = rt.route_id
        WHERE t.Trail_ID = ?
    """, trail_id)
    row = cursor.fetchone()

    if not row:
        return jsonify({'error': 'Trail not found'}), 404

    trail = {
        'TrailID': row[0],
        'Name': row[1],
        'Difficulty': row[2],
        'Length': row[3],
        'Location': row[4],
        'ElevationGain': row[5],
        'Summary': row[6],
        'Description': row[7],
        'RouteType': row[8],
        'Features': []
    }

    # Fetch features
    cursor.execute("""
        SELECT f.feature_name
        FROM CW2.Features f
        JOIN CW2.Trail_Feature_Map tfm ON f.feature_id = tfm.feature_id
        WHERE tfm.trail_id = ?
    """, trail_id)
    trail['Features'] = [feature[0] for feature in cursor.fetchall()]

    return jsonify(trail), 200



@app.route('/users', methods=['GET'])
def get_users():
    """
    Get all users
    Fetch all users from the database.
    ---
    tags:
      - Users
    responses:
      200:
        description: A list of users
    """
    cursor.execute("SELECT UserID, UserName, Email FROM CW2.Users")
    users = []
    for row in cursor.fetchall():
        users.append({
            'UserID': row[0],
            'UserName': row[1],
            'Email': row[2]
        })
    return jsonify(users), 200


@app.route('/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    """
    Get a user by ID
    Fetch a specific user by their UserID.
    ---
    tags:
      - Users
    parameters:
      - in: path
        name: user_id
        required: true
        type: integer
        description: The ID of the user to retrieve
    responses:
      200:
        description: The user's details
      404:
        description: User not found
    """
    cursor.execute("SELECT UserID, UserName, Email FROM CW2.Users WHERE UserID = ?", user_id)
    row = cursor.fetchone()
    if row:
        user = {
            'UserID': row[0],
            'UserName': row[1],
            'Email': row[2]
        }
        return jsonify(user), 200
    else:
        return jsonify({'error': 'User not found'}), 404


@app.route('/trails/<int:trail_id>', methods=['PUT'])
def update_trail(trail_id):
    """
      Update a trail
      This endpoint updates the details of a specific trail by its ID.
      ---
      tags:
        - Trails
      parameters:
        - in: path
          name: trail_id
          required: true
          type: integer
          description: The ID of the trail to update
        - in: body
          name: body
          schema:
            type: object
            properties:
              name:
                type: string
                example: "Updated Trail Name"
              difficulty:
                type: string
                example: "Moderate"
              length:
                type: number
                example: 5.0
              location:
                type: string
                example: "Updated Location"
              elevation_gain:
                type: number
                example: 150.0
              route_type:
                type: string
                example: "Loop"
              summary:
                type: string
                example: "Updated Summary"
              description:
                type: string
                example: "Updated Description"
      responses:
        200:
          description: Trail updated successfully
      """

    data = request.json

    if 'route_type' in data:
        cursor.execute("SELECT route_id FROM CW2.Route_Types WHERE route_name = ?", data['route_type'])
        route = cursor.fetchone()
        if not route:
            cursor.execute("INSERT INTO CW2.Route_Types (route_name) VALUES (?)", data['route_type'])
            conn.commit()
            cursor.execute("SELECT route_id FROM CW2.Route_Types WHERE route_name = ?", data['route_type'])
            route = cursor.fetchone()
        route_id = route[0]
        cursor.execute("UPDATE CW2.Trails SET route_id = ? WHERE trail_id = ?", route_id, trail_id)

    cursor.execute("""
        UPDATE CW2.Trails SET
            name = COALESCE(?, name),
            difficulty = COALESCE(?, difficulty),
            length = COALESCE(?, length),
            location = COALESCE(?, location),
            elevation_gain = COALESCE(?, elevation_gain),
            summary = COALESCE(?, summary),
            description = COALESCE(?, description)
        WHERE Trail_ID = ?
    """, data.get('name'), data.get('difficulty'), data.get('length'),
                   data.get('location'), data.get('elevation_gain'), data.get('summary'),
                   data.get('description'), trail_id)
    conn.commit()

    return jsonify({'message': 'Trail updated successfully'}), 200


# DELETE a trail
@app.route('/trails/<int:trail_id>', methods=['DELETE'])
def delete_trail(trail_id):
    """
       Delete a trail
       This endpoint deletes a specific trail by its ID.
       ---
       tags:
         - Trails
       parameters:
         - in: path
           name: trail_id
           required: true
           type: integer
           description: The ID of the trail to delete
       responses:
         200:
           description: Trail deleted successfully
       """

    try:
        cursor.execute("DELETE FROM CW2.Trail_Feature_Map WHERE trail_id = ?", trail_id)
        conn.commit()

        cursor.execute("DELETE FROM CW2.Trails WHERE Trail_ID = ?", trail_id)
        conn.commit()

        return jsonify({'message': 'Trail deleted successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    """
    Delete a user by ID
    Remove a specific user from the database by their UserID.
    ---
    tags:
      - Users
    parameters:
      - in: path
        name: user_id
        required: true
        type: integer
        description: The ID of the user to delete
    responses:
      200:
        description: User deleted successfully
      404:
        description: User not found
    """
    cursor.execute("DELETE FROM CW2.Users WHERE UserID = ?", user_id)
    if cursor.rowcount == 0:
        return jsonify({'error': 'User not found'}), 404
    conn.commit()
    return jsonify({'message': 'User deleted successfully'}), 200


@app.route('/')
def welcome():
    """
    Home
    Redirect to the Swagger documentation.
    ---
    tags:
      - Home
    responses:
      302:
        description: Redirect to Swagger UI
    """
    return "Welcome to the COMP2001 Trail Service! Go to /apidoc for Swagger UI."




# Run the Flask app
if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)

