# LINGO HANDS
### Video Demo: https://youtu.be/x-kNblgIX-Y
### Description:
Lingo Hands is a web application for learning American Sign Language (ASL). It uses a gamified approach to make learning much more fun. I was inspired by Duolingo; similarly, this application allows user registration and login, loss of lives for mistakes, and the accumulation of experience to unlock new lessons or levels, etc.

The application runs primarily in Python with Flask, HTML, CSS, JavaScript, and React with Three.js and the React Three Fiber library.

I chose Python with Flask because I find it easy and fast to use. I used Jinja to render HTML templates.

I also chose SQLite3 for its ease of use and because I'm comfortable with it thanks to what I learned in the course.

When planning this project, I wanted to add a 3D model to play the animation in American Sign Language (ASL) and looked for ways to do so.

At that time, I found this page: https://gltf.pmnd.rs/. This page transforms a 3D model in glb format into React JSX code similar to HTML. That's why I chose React: it's the simplest way to render 3D on the web with less code. Using pure JavaScript would require much more code and be more complex.

Communication between Python, Flask, and Jinja with the React component was complicated, so I opted for this approach:

```html
<script type="application/json" id="lesson-json">
{{ level_content | tojson | safe }}
</script>
<div id="lesson"></div>
<script type="module" src="/static/dist/assets/index.js"></script>
```
The script with id="lesson-json" stores the lesson or level information in JSON format.

The div with id="lesson" is where the React component is rendered.

The script is the React component compiled in JavaScript.

In the source code of the React component, `/lib/dummy/Lesson.jsx`, the JSON content of `lesson-json` is obtained using `document.getElementById("lesson-json")`, allowing for dynamic manipulation of the data within React.

## Installation and Setup

To run **Lingo Hands**, you need to set up the Python environment. Note that the React frontend is already compiled, so Node.js is only required if you wish to modify the source code.

#### 1. Backend Setup (Flask)

1. **Create a virtual environment:**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```


2. **Install dependencies:**
```bash
pip install -r requirements.txt
```


3. **Run the application:**
```bash
flask run
```

The app will be available at `http://127.0.0.1:5000`.

### 2. Frontend Development (Optional)

The app uses the pre-compiled JS in `static/dist`. To modify the React components:

1. Navigate to the source: `cd lib/dummy`
2. Install Node.js dependencies: `npm install`
3. Start development server: `npm run dev`
4. To update the app with changes: `npm run build`

### File structure

#### app.py:
Here you'll find all the logic for adding units, modules, levels, and content, as well as user registration and login.

To begin, this file includes the application's imports and configurations, and the Flask sessions.

##### index route:
Next, you'll find the `index` path with `@login_required`, located in the `herlpers.py` file, which we'll analyze later.

The `index` path displays all the course information and the details of the registered user. Here, all the course levels are represented as a zigzag path, and there's also a progress bar that shows the username, their current level, and the experience earned in the course to unlock more levels.

Also in the `index` path is the logic for recovering lost lives, which occurs every 30 minutes.

If the user runs out of lives, they won't be able to access any levels until they recover some.

If the user has already completed a level, it will be displayed in green to indicate completion. The user can repeat completed levels and will not receive penalties or XP for doing so.

##### level route:
Next, we have the level or lesson details route. This route has two methods: POST and GET. The GET method renders the level template with the level information (`level_content`). Obviously, we first check that the user has the required experience and enough lives; otherwise, we return them to the waiting room.

The content template is important because it renders the React JS component with the lesson logic (quiz and learning), supported by the dummy 3D scene.

The source code for the dummy scene and the 3D scene is located in /lib/dummy.

Then we have the POST method, which checks if the user completed the level or lesson and applies the corresponding penalty: losing a life or gaining experience for completing it. If incorrect answers outnumber correct answers, the user fails the lesson and loses a life. However, if they complete it, they receive 1 experience point to unlock the next level.

##### dashboard route:
This path is only accessible to users with administrator privileges. Here, the administrator can add and remove units, modules, levels, etc.

##### login, register and logout routes:
The implementation is a copy and paste of `CS50 Finance`, the only difference is that in the login we save the role in the cookies.

##### api and api/delete routes:
There are several routes that use "api" as a prefix. These routes are used to add "units, modules, levels, and content_level" from the dashboard template using forms with actions.

There are also similar routes that use "api" and "delete" as prefixes. These are specifically used to delete units, modules, etc., respectively.

These routes require administrator privileges.

#### helpers.py:
Aquí hay otra copia y pega de "CS50 Finance", pero con un nuevo decorador llamado "admin required". Este también comprueba si el usuario ha iniciado sesión y solo otorga acceso si tiene el rol de administrador.

#### asl.db:
This is the application's database, which contains these tables:

- content_level
- modules
- user_progress
- levels
- units
- users

schemas:

CREATE TABLE users (
id INTEGER PRIMARY KEY AUTOINCREMENT,
username TEXT NOT NULL UNIQUE,
hash TEXT NOT NULL,
role TEXT CHECK(role IN ('admin', 'user')),
xp INTEGER DEFAULT 0,
lives INTEGER DEFAULT 3,
last_hearth_loss DATETIME
);

CREATE TABLE units
(
id INTEGER PRIMARY KEY AUTOINCREMENT,
title TEXT NOR NULL,
order_index INTEGER,
description TEXT
);

CREATE TABLE modules (
id INTEGER PRIMARY KEY AUTOINCREMENT,
unit_id INTEGER,
title TEXT NOT NULL,
order_index INTEGER,
FOREIGN KEY (unit_id) REFERENCES units(id) ON DELETE CASCADE
);

CREATE TABLE levels (
id INTEGER PRIMARY KEY AUTOINCREMENT,
module_id INTEGER,
title TEXT NOT NULL,
order_index INTEGER,
required_xp INTEGER DEFAULT 0,
FOREIGN KEY (module_id) REFERENCES modules(id) ON DELETE CASCADE
);

CREATE TABLE level_content (
id INTEGER PRIMARY KEY AUTOINCREMENT,
level_id INTEGER,
step_type TEXT CHECK(step_type IN ('learn', 'quiz')), 
sign_id TEXT NOT NULL,
meaning TEXT,
instructions TEXT,
option_a TEXT,
option_b TEXT,
option_c TEXT,
correct_option TEXT,
order_index INTEGER,
FOREIGN KEY (level_id) REFERENCES levels(id) ON DELETE CASCADE
);

CREATE TABLE user_progress (
user_id INTEGER,
level_id INTEGER,
completed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
PRIMARY KEY (user_id, level_id),
FOREIGN KEY (user_id) REFERENCES users(id),
FOREIGN KEY (level_id) REFERENCES levels(id)
);


#### templates folder:
`apology.html`
`dashboard.html`: where all the content of the ASL course is managed.

`index.html`: where the average user can take the ASL course and have fun; it shows the path to follow.

`layout.html`: contains the header, footer, and alert. The header will display different links depending on whether the user is logged in or has administrator privileges.

`level.html`: contains the React JS component that has all the lesson logic, such as quizzes and learning lessons, and is responsible for rendering the 3D scene with the dummy that helps us reproduce ASL signs.

`login.html and register.html`: is the same as in `CS50 Finance` but with a different style.

#### lib/dummy folder:
`main.jsx`: The entry point for the React application.

`Lesson.jsx`: All the lesson logic, such as verifying user answers, conditional rendering of the lesson type (e.g., "learn" or "quiz"), etc.

`Scene.jsx`: A 3D scene using the React Three Fiber library, including lighting, positioning, camera, and dummy elements.

`Dummy.jsx`: Code generated by https://gltf.pmnd.rs/ that converts a model created in Blender or downloaded from the internet in GLB format to JSX.

#### static folder:
`styles`: Application CSS styles, all done manually. I already had experience in frontend development; I completed courses on algorithms, low-level code, and backend development.

`dist`: Compiled React code files in lib/dummy