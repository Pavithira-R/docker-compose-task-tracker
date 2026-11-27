## Task Tracker with Docker Compose

A responsive task management application built with Flask and PostgreSQL. Docker Compose manages the application and database as separate services.

Users can create, complete, reopen, and delete tasks. PostgreSQL stores tasks in a persistent Docker volume.

### Features

- Add tasks with titles up to 200 characters.
- Mark tasks as complete or reopen them.
- Delete tasks.
- Responsive interface for desktop and mobile screens.
- Persistent database storage.
- CSRF protection for forms.
- Health checks for the application and database.
- Application container runs as a non-root user.

### Technologies

| Technology | Purpose |
|---|---|
| Python and Flask | Application backend |
| HTML, CSS, and Jinja | Responsive user interface |
| Flask-SQLAlchemy | Database models and queries |
| PostgreSQL | Task storage |
| Flask-WTF | CSRF protection |
| Gunicorn | Application server |
| Docker Compose | Service configuration and management |

### Architecture

The browser accesses the Flask application on localhost port 8082.
The application connects to PostgreSQL using the Compose service name `db`.

| Service | Description | Ports |
|---|---|---|
| `web` | Flask application served by Gunicorn | Laptop `8082` → container `8000` |
| `db` | PostgreSQL 17 database | Container `5432`; not published to the laptop |

Compose waits for the database health check to pass before starting the application. The application initializes its database tables before starting Gunicorn.

The webpage is bound to `127.0.0.1` for local access.

### Project Files

| File | Purpose |
|---|---|
| `app.py` | Application routes, database model, and health endpoint |
| `templates/index.html` | Webpage template and responsive styles |
| `requirements.txt` | Python dependencies |
| `Dockerfile` | Application image build instructions |
| `compose.yaml` | Application, database, health checks, and volume configuration |
| `.env.example` | Example environment configuration |
| `.gitignore` | Files excluded from Git |
| `.dockerignore` | Files excluded from the Docker build context |
| `README.md` | Setup and usage documentation |

### Prerequisites

- Git
- Docker Desktop with the engine running
- Docker Compose

Verify Compose is available:

```sh
docker compose version
```

Python and PostgreSQL do not need to be installed on the host because they run inside containers.

### Setup

Clone the repository:

```sh
git clone https://github.com/Pavithira-R/docker-compose-task-tracker.git
cd docker-compose-task-tracker
```

Create your local environment file.

On Windows PowerShell:

```powershell
Copy-Item .env.example .env
notepad .env
```

On macOS or Linux:

```sh
cp .env.example .env
```

Edit `.env` and replace both placeholders:

```dotenv
POSTGRES_USER=taskuser
POSTGRES_DB=tasktracker
POSTGRES_PASSWORD=replace_with_your_own_random_password
SECRET_KEY=replace_with_your_own_random_secret
```

Use a new random password for this project's database and a different random value for the Flask secret key.

Keep `.env` private. Never commit it to Git.

### Build and Run

Validate the Compose configuration:

```sh
docker compose config --quiet
```

Build and start both services:

```sh
docker compose up -d --build
```

Check their status:

```sh
docker compose ps
```

Wait until both services show `healthy`, then open:

http://localhost:8082

### Using the Application

1. Enter a task and select **Add task**.
2. Select **Complete** to mark it as done.
3. Select **Undo** to reopen a completed task.
4. Select **Delete** to remove a task.

This learning application does not include user accounts. Anyone with access to the application can manage its tasks.

### Health Check

Open:

http://localhost:8082/health

When the application can connect to PostgreSQL, it returns HTTP 200:

```json
{"status": "healthy"}
```

If the database check fails, it returns HTTP 503.

### Verify Persistent Storage

1. Add a task in the application.
2. Remove the containers:

```sh
docker compose down
```

3. Recreate them:

```sh
docker compose up -d
```

4. Wait for the services to become healthy and refresh the webpage.

The task should still appear because PostgreSQL data is stored in the named volume `postgres_data`.

**Warning:** `docker compose down -v` deletes the database volume and its saved tasks.

### Useful Commands

View service status:

```sh
docker compose ps
```

View logs:

```sh
docker compose logs --tail=100
```

Follow application logs:

```sh
docker compose logs -f web
```

Press Ctrl+C to stop following logs; the containers keep running.

Stop services without removing containers:

```sh
docker compose stop
```

Start existing stopped containers:

```sh
docker compose start
```

Remove containers and the project network while keeping database data:

```sh
docker compose down
```

Rebuild after changing application code or dependencies:

```sh
docker compose up -d --build
```

### Troubleshooting

**Cannot connect to the Docker engine**

Open Docker Desktop and wait until its engine is running, then retry.

**Port 8082 is already in use**

Stop the application using that port or change the Compose port mapping to:

```yaml
ports:
  - "127.0.0.1:8084:8000"
```

Then run `docker compose up -d` and open http://localhost:8084.

**Application does not become healthy**

Check the service status and logs:

```sh
docker compose ps
docker compose logs --tail=100 web db
```

Do not publish logs containing credentials.

**Database password changed after the first run**

PostgreSQL initialization settings apply when its data directory is first created. Editing `.env` alone does not change the password of an existing database user.

Restore the original configuration or update the database user's password deliberately. Do not delete the volume unless you intend to erase its data.

### Verification Completed

- Built the application image successfully.
- Started the application and database with Docker Compose.
- Confirmed both services reported healthy.
- Tested task creation, completion, reopening, and deletion.
- Confirmed tasks remained saved after containers were recreated.

  ### CI/CD Pipeline

GitHub Actions builds the application and starts PostgreSQL in an isolated test environment.
The pipeline runs four automated tests covering database health, task creation/completion/reopening/deletion, empty input validation, and CSRF protection.
Pull requests run the build and tests. Successful pushes to main also publish the tested image to Docker Hub with latest and commit-specific tags.
Docker Hub credentials are stored in GitHub Actions secrets. Temporary test containers and volumes are removed afterward.
Server deployment is handled separately.

### AWS Deployment

Deployed on an Ubuntu 24.04 LTS EC2 instance in Mumbai
(ap-south-1), using Docker Engine and Docker Compose.

The standalone `compose.aws.yaml` configuration pulls the
published application image from Docker Hub and runs it
alongside PostgreSQL.

#### Server Setup

Install Docker Engine and the Compose plugin, clone this
repository, and enter its directory.

Create a private `.env` file containing:

- POSTGRES_USER
- POSTGRES_DB
- POSTGRES_PASSWORD
- SECRET_KEY

Use separate random values for the database password and
Flask secret key. Restrict file permissions:

```sh
chmod 600 .env
```

Never commit `.env` or SSH private keys.

#### Start the Deployment

```sh
sudo docker compose -f compose.aws.yaml config --quiet
sudo docker compose -f compose.aws.yaml pull
sudo docker compose -f compose.aws.yaml up -d --wait --wait-timeout 180
```

#### Verify the Deployment

```sh
sudo docker compose -f compose.aws.yaml ps
curl -fsS http://localhost:8082/health
```

Both services should report healthy. The health endpoint
returns HTTP 200 with `{"status":"healthy"}`.

Visit `http://<EC2-public-IP>:8082` from an allowed connection.

#### Network Access

The EC2 security group allows:

| Port | Purpose | Source |
|---|---|---|
| 22 | SSH administration | My public IPv4 address /32 |
| 8082 | Application access | My public IPv4 address /32 |

PostgreSQL port 5432 is not published on the server.

This is an HTTP practice deployment with access restricted
to my IP. It does not yet include HTTPS or user accounts.
Reviewers require a separately authorized source IP to access it.

The public IP may change after stopping and starting EC2.

#### Data and Cost Management

PostgreSQL data is stored in a named Docker volume.

Stop the EC2 instance between practice sessions to reduce
compute usage. EBS storage continues to incur costs while
the instance is stopped.

Do not run `docker compose down -v` unless you intend to
delete the saved database.

Back up required data before terminating the instance and
deleting its storage.

### Project Scope

This project demonstrates a local Docker Compose application with database integration and persistent storage.

Cloud deployment, automated deployment, and monitoring dashboards are planned extensions.

### Author

Pavithira Rajkumar
