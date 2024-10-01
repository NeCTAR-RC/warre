# For more information, please refer to https://aka.ms/vscode-docker-python
FROM python:3.12-slim-bookworm

EXPOSE 5000

# Keeps Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE=1

# Turns off buffering for easier container logging
ENV PYTHONUNBUFFERED=1

# Install pip requirements
COPY requirements.txt .

RUN apt-get update && apt-get install -y gcc

RUN python -m pip install -c https://releases.openstack.org/constraints/upper/2024.1 -r requirements.txt
RUN python -m pip install -c https://releases.openstack.org/constraints/upper/2024.1 gunicorn

WORKDIR /app
COPY dist/* /app

RUN python -m pip install -c https://releases.openstack.org/constraints/upper/2024.1 *.tar.gz && rm *.tar.gz

# Creates a non-root user and adds permission to access the /app folder
# For more info, please refer to https://aka.ms/vscode-docker-python-configure-containers
RUN useradd -u 42420 appuser && chown -R appuser /app
USER appuser

# During debugging, this entry point will be overridden. For more information, please refer to https://aka.ms/vscode-docker-python-debug
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--access-logfile=-", "--worker-tmp-dir", "/dev/shm", "--workers", "2", "warre.wsgi:application"]
