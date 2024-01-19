# Development Workflow

To speed up the local development workflow for amanuensis, alongside the gen3 stack, follow these steps.

1) Build the image using Dockerfile.dev:
```
docker build -f Dockerfile.dev -t amanuensis:test .
```

2) In the docker-compose.yml file inside the compose-services repo:

    1) Make sure amanuensis-service is using the amanuensis:test image.
    2) Under amanuensis-service volumes property, map your local source-code repo to the amanuensis/amanuensis directory. The order is source:target.

    ```
    - /location-of-your-repos/amanuensis/amanuensis:/amanuensis/amanuensis
    ``` 
    
3) Inside compose-services run ```docker compose up``` to start all services of the gen3 stack.

4) Open a shell to the amanuensis:test container. Navigate to /amanuensis/amanuensis and run ```bash watch-files.sh```. This will watch for files changes in this directory and re-run the uwsgi command every time there is a file change, which will ensure that changes are reflected in the container almost immediatelly.

## Debugging

Once you run ```bash watch-files.sh``` most of the output will show in that same terminal window. Information about HTTP requests--method, URL, etc.--will continue to show up in the Docker logs.

## Development Tools

The Docker.dev file installs inotify-tools to allow the watch-files.sh script to check for file changes. In addtition, it will install vim.

To use bash instead of the default, sh, run ```exec /bin/bash``` in the container or if starting from the host terminal run: 

    docker exec -it amanuensis-service /bin/bash


python -m venv env

source env/bin/activate

poetry install

alembic revision -m "add_save"