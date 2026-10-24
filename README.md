# RetinaTransform — AI-Powered Retinal Screening

## Meet the Team

### An Interdisciplinary Team from the University of Leeds

RetinaTransform is being developed by a team of four students from the **University of Leeds** as part of the AI in Healthcare Hackathon organised by Leeds Artificial Intelligence Society. Bringing together expertise from computer science and mechanical engineering, our team combines software development and engineering perspectives to explore how AI can support healthcare screening workflows.

| Team Member | University of Leeds ID | School |
|---|---|---|
| **Khudayar Khudiyev** | `lvhh0513` | School of Computer Science |
| **Yuta Tsutsumi** | `rwjq0840` | School of Computer Science |
| **Hibaq Omar** | `lhqg0050` | School of Mechanical Engineering |
| **Kunwar Ranjeet** | `bcjp0382` | School of Computer Science |

We all four team members are students at the **University of Leeds, United Kingdom**.

### Our Collaboration

Our team brings together complementary perspectives to build a healthcare-focused AI prototype:

- **Computer Science:** Software engineering, application development, backend services, and AI system integration.
- **Mechanical Engineering:** An engineering perspective on system design, practical problem-solving, and interdisciplinary innovation.
- **Collaborative development:** Working together to integrate the web application, authentication services, and retinal screening interface into one cohesive prototype.

Through this project, we aim to demonstrate how interdisciplinary collaboration can translate an AI healthcare concept into a working technical prototype, while keeping usability, responsible AI, and clinical limitations in view.

**Hackathon:** AI in Healthcare Hackathon  
**Organiser:** Leeds Artificial Intelligence Society  
**Institution:** University of Leeds  
**Location:** Helix, Leeds, United Kingdom  
**Event dates:** 24–25 October 2026


RetinaTransform is a healthcare-focused software project that brings together a modern web interface, secure user authentication, and an AI-powered retinal screening application. The project is being developed for the AI in Healthcare Hackathon at the University of Leeds, where medical and engineering students collaborate to explore practical solutions to real clinical challenges.

The application combines **React, Node.js, SQLite, and Streamlit** into a modular architecture. React provides the user-facing interface, Node.js and SQLite support authentication and account management, and Streamlit hosts the retinal screening workflow.

> **Clinical responsibility:** RetinaTransform is a hackathon prototype intended to explore AI-assisted retinal screening. It is not a substitute for professional medical assessment, and its outputs should not be treated as a definitive diagnosis.

---

## 1. Project Overview and Folder Structure

### 1.1 Project Overview

Retinal diseases can affect vision and may require timely clinical assessment. AI-assisted image analysis offers an opportunity to support screening workflows by helping process retinal images and present model-generated results to users.

RetinaTransform explores this approach through a modular application that connects a web-based interface with a dedicated retinal screening component.

The project is organised around three main components:

- **Frontend:** A React application that provides the user interface and navigation.
- **Backend:** A Node.js and Express API that manages user authentication and communicates with an SQLite database.
- **AI screening application:** A Streamlit application that provides the retinal screening interface and loads the configured machine-learning model.

This separation keeps the user interface, authentication logic, and AI screening workflow independently manageable.

### 1.2 Project Objectives

The primary objectives of the project are to:

1. Develop an accessible, web-based interface for a healthcare screening workflow.
2. Implement account registration, login, session management, and logout.
3. Integrate an AI screening interface into the main web application.
4. Maintain a modular architecture that supports independent development and testing.
5. Establish a foundation for future improvements in model integration, clinical usability, security, and explainability.

### 1.3 Technology Stack

| Component | Technology | Responsibility |
|---|---|---|
| Frontend | React, Vite, JavaScript | User interface and navigation |
| Backend | Node.js, Express.js | REST API and authentication |
| Database | SQLite | Persistent user and account data |
| Authentication | bcrypt, JSON Web Tokens (JWT), HTTP-only cookies | Password hashing and session authentication |
| AI interface | Streamlit, Python | Retinal screening workflow |
| Model integration | ONNX Runtime / ONNX model | Loading and running the configured screening model |
| Development | npm, Python, environment variables | Dependency management and local configuration |

*The table describes the current project architecture and intended integration points. Actual model availability and runtime behaviour depend on the local model files and installed dependencies.*

### 1.4 Repository Folder Structure

The main project is organised as follows:

```text
Hackathon-2026-leeds-main/
│
├── central-system/
│   │
│   ├── frontend/
│   │   ├── src/
│   │   │   ├── App.jsx
│   │   │   ├── config.js
│   │   │   └── ...
│   │   ├── .env
│   │   ├── .env.example
│   │   ├── package.json
│   │   └── vite.config.js
│   │
│   └── backend/
│       ├── server.js
│       ├── data/
│       │   └── retinatransform.sqlite
│       ├── .env
│       └── package.json
│
├── retina-screening-main/
│   ├── retina_app/
│   │   └── retina_app.py
│   └── models/
│       └── branchA_v1.onnx
│
└── README.md
```

**Important notes:**

- The structure above highlights the main components; additional source files, assets, configuration files, and dependencies may exist in the repository.
- The SQLite database is created or used according to the backend configuration. The database file may not exist until the backend initialises it.
- The `branchA_v1.onnx` file is the expected model location. The model weights must be obtained from the appropriate project source if they are not included in the repository.
- Never commit passwords, production secrets, private datasets, or sensitive patient information to version control.

---

## 2. React, Node.js/SQLite, and Streamlit Architecture

### 2.1 System Architecture

RetinaTransform follows a modular architecture in which the frontend, authentication backend, database, and screening application have separate responsibilities.

```text
                   USER
                     |
                     v
          +----------------------+
          |   React Frontend     |
          |       Vite           |
          |    Port 5174         |
          +----------------------+
              |             |
              |             |
      /api requests     Screening iframe
              |             |
              v             v
   +----------------+  +-------------------+
   | Node.js /      |  | Streamlit App      |
   | Express API    |  | Port 8501          |
   | Port 5000      |  | Python             |
   +----------------+  +-------------------+
              |                   |
              v                   v
   +----------------+  +-------------------+
   | SQLite         |  | ONNX Model         |
   | User Accounts  |  | Model Inference    |
   +----------------+  +-------------------+
```

The frontend communicates with the backend through HTTP API requests. The screening interface is embedded in the frontend using an iframe, allowing the screening application to run separately while remaining accessible from the main interface.

The diagram represents the current integration approach. The React frontend and Streamlit application are separate services; embedding Streamlit does not automatically share the frontend's authentication session with the screening application.

### 2.2 React Frontend

The frontend is built with React and Vite.

Its responsibilities include:

- Rendering the main application interface.
- Providing login and registration screens.
- Sending authentication requests to the backend.
- Displaying relevant success and error messages.
- Embedding the Streamlit screening interface.
- Providing navigation between the available application sections.

The frontend uses environment variables to configure the backend API and screening application URLs.

During local development, Vite runs on port `5174`. API requests can be proxied to the backend on port `5000`, allowing the frontend to use same-origin paths such as `/api/v1/auth/login`.

### 2.3 Node.js and Express Backend

The backend provides the application's authentication API using Node.js and Express.

Its responsibilities include:

- Handling user registration and login requests.
- Validating incoming request data.
- Hashing passwords using bcrypt rather than storing plaintext passwords.
- Verifying credentials during login.
- Issuing and validating JWT-based authentication sessions.
- Setting an HTTP-only session cookie.
- Returning the authenticated user's information.
- Supporting logout and health-check endpoints.

The backend listens on `127.0.0.1:5000` in the current local development configuration.

The principal authentication endpoints are:

| Method | Endpoint | Purpose |
|---|---|---|
| `POST` | `/api/v1/auth/register` | Register a user account |
| `POST` | `/api/v1/auth/login` | Authenticate a user |
| `GET` | `/api/v1/auth/me` | Retrieve the current session's user |
| `POST` | `/api/v1/auth/logout` | End the current session |
| `GET` | `/health` | Check backend availability |

The exact request fields and response formats should be confirmed against the backend implementation.

### 2.4 SQLite Database

SQLite provides lightweight, file-based persistence for the backend.

The database path is configurable through the backend environment variables. The current configuration uses:

```text
central-system/backend/data/retinatransform.sqlite
```

The backend is responsible for creating, querying, and updating the database as required by its implementation.

SQLite is suitable for local development and a hackathon prototype because it does not require a separately managed database server. A production deployment would require an assessment of concurrent access, backups, access controls, deployment persistence, and operational requirements.

### 2.5 Streamlit Retinal Screening Application

The AI screening component is implemented in Python using Streamlit.

Its responsibilities include:

- Providing a dedicated screening interface.
- Supporting the configured image-analysis workflow.
- Loading the expected ONNX model.
- Presenting the results generated by the configured screening pipeline.

The application is expected to run locally on port `8501`.

The expected model path is:

```text
retina-screening-main/models/branchA_v1.onnx
```

**Model availability is a prerequisite for functional inference.** If the model file is absent, the screening application may display a model-loading error. The existence of an interface alone does not establish that the model is trained, clinically validated, or producing medically reliable results.

### 2.6 How the Components Work Together

A typical application flow is:

1. A user opens the React frontend.
2. The user submits login or registration details.
3. React sends the request to the Express API.
4. The backend validates the request and interacts with SQLite when required.
5. Following successful login, the backend establishes the authentication session through its configured cookie mechanism.
6. The user accesses the screening interface embedded in the React application.
7. Streamlit executes the configured screening workflow independently and uses the model file when available.
8. The screening application presents its generated output through its own interface.

**Current integration limitation:** The iframe provides interface integration, not automatic authentication integration. The Streamlit application does not automatically inherit the React application's authenticated identity or permissions. Any requirement for authenticated screening access must be implemented and tested separately.

---

## 3. Environment Configuration and Installation

### 3.1 Prerequisites

Install the following tools before starting the project:

- Node.js and npm, using versions compatible with the project's `package.json` files.
- Python 3 and `pip`.
- Git, if cloning the repository.
- The Python packages specified by the screening application's dependency files.
- The required ONNX model file, if model inference is to be tested.

Check the installed versions:

```bash
node --version
npm --version
python3 --version
```

### 3.2 Configure the Backend Environment

Create or update the backend environment file:

**Location:** `central-system/backend/.env`

```dotenv
PORT=5000
SQLITE_PATH=./data/retinatransform.sqlite
JWT_SECRET=replace_with_a_random_secret_of_at_least_32_characters
APP_ORIGIN=http://localhost:5174
NODE_ENV=development
```

Configuration details:

- `PORT` specifies the backend port.
- `SQLITE_PATH` specifies the database file location.
- `JWT_SECRET` is used to sign and verify authentication tokens. The current backend requires a secret of at least 32 characters.
- `APP_ORIGIN` specifies the permitted frontend origin for the current local setup.
- `NODE_ENV` identifies the development environment.

Generate a suitable local secret with Python:

```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

Copy the generated value into `JWT_SECRET`.

Keep `.env` files private and excluded from Git. Use separate secrets and appropriate configuration for production.

### 3.3 Configure the Frontend Environment

Create or update the frontend environment file:

**Location:** `central-system/frontend/.env`

```dotenv
CENTRAL_API_PROXY_TARGET=http://localhost:5000
VITE_CENTRAL_API_BASE=
VITE_DATA_MODE=live
VITE_SCANNER_URL=http://localhost:8501
CENTRAL_WEB_PORT=5174
```

Configuration details:

- `CENTRAL_API_PROXY_TARGET` tells Vite where to forward API requests.
- `VITE_CENTRAL_API_BASE` is left empty so the frontend can use same-origin API paths through the Vite proxy.
- `VITE_DATA_MODE=live` selects the live API configuration rather than mock data.
- `VITE_SCANNER_URL` specifies the Streamlit application URL used by the frontend.
- `CENTRAL_WEB_PORT` specifies the intended frontend development port.

Vite environment variables prefixed with `VITE_` are exposed to client-side code. Do not place passwords, private keys, or other secrets in frontend environment variables.

Restart the frontend development server after changing its environment file.

### 3.4 Install Backend Dependencies

Open a terminal at the backend directory:

```bash
cd central-system/backend
npm install
```

Ensure the backend `.env` file is configured before starting the API.

Start the backend using the start script defined in `package.json`. If no start script exists, use the project's actual entry point:

```bash
node server.js
```

The API should be available at:

```text
http://localhost:5000
```

Check the health endpoint:

```bash
curl http://localhost:5000/health
```

The response format depends on the implementation of the health endpoint.

### 3.5 Install Frontend Dependencies

Open a second terminal:

```bash
cd central-system/frontend
npm install
```

Start the Vite development server:

```bash
npm run dev
```

The frontend is configured to run at:

```text
http://localhost:5174
```

If Vite reports that the port is occupied, stop the conflicting process or resolve the port configuration before continuing. Keep the frontend URL consistent with the backend's `APP_ORIGIN` setting.

### 3.6 Install Streamlit Dependencies

Open a third terminal:

```bash
cd retina-screening-main
python3 -m venv .venv
```

Activate the virtual environment.

**macOS / Linux:**

```bash
source .venv/bin/activate
```

**Windows PowerShell:**

```powershell
.venv\Scripts\Activate.ps1
```

Install the dependencies specified by the project:

```bash
pip install -r requirements.txt
```

Run this command from the directory containing the screening application's `requirements.txt`. If the dependency file is located elsewhere, use its actual path. If no requirements file is supplied, install the dependencies documented by the project rather than assuming a package list.

Start Streamlit:

```bash
streamlit run retina_app/retina_app.py --server.port 8501
```

The screening interface should be available at:

```text
http://localhost:8501
```

### 3.7 Start the Complete Application

For local development, run the three services in separate terminals.

| Service | Command | Local URL |
|---|---|---|
| Backend API | `node server.js` | `http://localhost:5000` |
| React frontend | `npm run dev` | `http://localhost:5174` |
| Streamlit screening | `streamlit run retina_app/retina_app.py --server.port 8501` | `http://localhost:8501` |

Start each command from the appropriate project directory and ensure that all required environment files and dependencies are configured.

Once the services are running, open the React frontend. Test authentication independently, then check whether the embedded screening interface loads and whether the required model is available.

### 3.8 Installation and Configuration Checks

Before considering the local setup complete, verify the following:

- [ ] Backend dependencies are installed.
- [ ] The backend `.env` file contains a valid secret and the correct frontend origin.
- [ ] The backend health endpoint responds successfully.
- [ ] The SQLite database is created or accessible at the configured path.
- [ ] Frontend dependencies are installed.
- [ ] The frontend runs on port `5174`.
- [ ] The Vite API proxy points to the backend on port `5000`.
- [ ] Login, registration, session retrieval, and logout are tested.
- [ ] The Streamlit application starts on port `8501`.
- [ ] The frontend iframe points to the correct Streamlit URL.
- [ ] The required ONNX model file exists and can be loaded before testing inference.

If the screening application reports that the model file cannot be found, verify the configured model path and obtain the required model weights. Installing the software dependencies alone does not supply missing model files.

