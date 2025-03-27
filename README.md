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

## END OF DEPRECATED ##

# Development Workflow

## building and running the container locally using Helm

1) Follow the steps provided in the confluence page `Using Helm for local development` to set up and run a local kubernetes cluster using Helm 

2) run ` nerdctl --namespace k8s.io build -f Dockerfile.dev -t amanuensis:test . ` This will create a image in your rancher Desktop app

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

## Generating config

run python cfg_help.py create and a default config file will be created in ~/.gen3/amanuensis/ 

## Installing Dependencies

python -m venv env

source env/bin/activate

poetry install

## Migrating DB

1) Migrate DB

    upgrade: `alembic upgrade head` or revision id instead of head

    downgrade: `alembic downgrade base` or revision id instead of base

2) create new revision

    `alembic revision -m <name of revision>`

## Run tests

1) in order to pass all the tests in "test_2_check_validate_filter_sets.py" you will need the gitops.json file from the configuration-files repo
   and the es_to_dd_map.json file which can be generated in the elasticsearch folder of the gen3_etl repo.

2) in the config fill in the value DB, AWS_CREDENTIALS with your values and ARBORIST with 'http://arborist-service'. 

3) create and/or activate the virtual env and run poetry install

4) pytest --order-scope=module --disable-warnings --configuration-file="<config-file.yaml>" 
    --order-scope (required) some tests need to clear DB tables
    --disable-warnings (optional) mutes warnings
    --configuration-file (required/optional) required if multiple config files exist in search folders, optional if only 1 exists 
                                             the default value is amanuensis-config.yaml
                                              

## Mocking

    all the mocking fixtures for Fence, Arborist and PcdcAnalysisTools are found in conftest

    fixtures:

            1) fence_users(): this holds list which is used to mock the Users table in the fence DB

            2) register_user(email, name, role="user"): this adds a new user to fence_users,

                email: fills in the name column
                name: used to fill in other personal information columns from the Users table
                role: (optional) used to allow access to admin endpoints in amanuensis

            3) find_fence_user(): returns a function that can be used to mock the fence_get_users in resources/fence/__init__.py
                                  the function takes an input in the format {"ids": [list of ids]} or {"usernames": [list of names]}
                                  the input will return users from the fence_users fixture
                                  note: usernames looks through the names column of the fence Users which is the email of a register user

            4) login(): returns a function the takes and id and email and patches the current_user object with those values

            5) mock_requests_post() patches the request object that sends post requests to "http://fence-service/admin/users/selected" which returns
                                    a user or users from fence_users() and 'http://pcdcanalysistools-service/tools/stats/consortiums' which returns
                                    a list of consortiums provided. example mock_requests_post(consortiums=["INRG"]) will return ["INRG"].
                                    alternative urls and status codes can also be provided for instance mock_requests_post(urls={'http://pcdcanalysistools-service/tools/stats/consortiums', 403})
                                    will return a 403 response code
            
            6) patch_auth_request() automatically created at the beginning of a test session and applies to all tests. It mocks app.aborist.auth_request object
                                    which is called in the has_arborist_access() method and the admin decorator on routes. it takes the Authorization header from
                                    the request in the format "Authorization": 'bearer {fence_id}' and looks for a user in fence_users using the fence_id and 
                                    return True if the users role is admin else False. This is used to mock arborist

            7) client(): used to send http request to server

            8) session(): used to interact with DB

            9) s3(): creates a bucket using provided AWS_CREDS in config, automatically deletes bucket at end of test file 