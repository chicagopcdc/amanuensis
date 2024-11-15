# Development Workflow

## DEPRECATED ##
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

## DEPRECATED ##

1) Follow the steps provided in the confluence page `Using Helm for local development` to set up and run a local kubernetes cluster using Helm 

2) run ` nerdctl --namespace k8s.io build -f Dockerfile.dev amanuensis:test . ` This will create a image in your rancher Desktop app

3) in pcdc-default-values.yaml or default-values.yaml (depending on which version of gen3-helm you are using) replace the amanuensis section with this:

    amanuensis:
        image:
            repository: "amanuensis"
            tag: "test"
            pullPolicy: Never

4) run `pcdc roll` or if you already have rolled out the deployment run `pcdc roll amanuensis`


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

## Run tests

1) in the config fill in the value DB, AWS_CREDENTIALS with your values and ARBORIST with 'http://arborist-service'

2) activate the virtual env

3) pytest --order-scope=module

## Mocking

    all the mocking fixtures for Fence, Arborist and PcdcAnalysisTools are found in conftest

    1) Fence

        pass an email, name and optional "admin" to the register_user() fixture to add a user to fence

        the fence users are stored in the fence_users fixture and resets every time the tests are run

        the fence_get_users method is mocked by default and will search through the fence_users fixture instead of sending a request to fence.
        fence_get_users inputs are the same as the unmocked version


    2) Arborist

        to mock current_user use the login() fixture and pass a id and username (email) to mock current_user.id and current_user.username throughout
        amanuensis. This will reset by default at the end of a test function but can be overridden by calling login again
 
        the endpoints with the admin decorator or functions that use the has_arborist_access() function can be bypassed by passing the header 
        "Authorization": 'bearer {fence_id}' where fence_id is the ID of a fence_user who is an admin that you created using register_user().
    

    2) using the patch function from the mock library
    
        patch("path where object is called", return_value="fake return value")

        patch("path where object is called", side_effect="A method to replace the orignal")

        patch.object("path where object is called", "attribute to change", (either return_value or side_effect)="mocked value")

        make sure to use the path where the object is called not definied

        example: patch('amanuensis.resources.consortium_data_contributor.get_consortium_list', ["INRG"]) 
