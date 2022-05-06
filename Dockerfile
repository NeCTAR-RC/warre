# For more information, please refer to https://aka.ms/vscode-docker-python
FROM python:3.8-slim-bullseye

EXPOSE 5000

# Keeps Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE=1

# Turns off buffering for easier container logging
ENV PYTHONUNBUFFERED=1

# Install pip requirements
COPY requirements.txt .

RUN apt-get update && apt-get install -y gcc

RUN python -m pip install -c https://releases.openstack.org/constraints/upper/yoga -r requirements.txt
RUN python -m pip install -c https://releases.openstack.org/constraints/upper/yoga gunicorn 

WORKDIR /app
COPY . /app

RUN python -m pip install -c https://releases.openstack.org/constraints/upper/yoga -e /app

# Creates a non-root user and adds permission to access the /app folder
# For more info, please refer to https://aka.ms/vscode-docker-python-configure-containers
RUN useradd -u 42420 appuser && chown -R appuser /app
USER appuser

# During debugging, this entry point will be overridden. For more information, please refer to https://aka.ms/vscode-docker-python-debug
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "warre.wsgi:application"]
