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

## Run Endpoint tests

1) in the config fill in ARBORIST with 'http://arborist-service'

2) activate the virtual env

3) pytest tests_endpoints/endpoints

4) pytest tests_endpoints/resources

## How to build endpoint tests

1) mocking: 
    1) all initiated variables, functions, objects and attributes can be mocked

    2) using the patch function from the mock library
    
        patch("path where object is called", return_value="fake return value")

        patch("path where object is called", side_effect="A method to replace the orignal")

        patch.object("path where object is called", "attribute to change", (either return_value or side_effect)="mocked value")

        make sure to use the path where the object is called not definied

        example: patch('amanuensis.resources.consortium_data_contributor.get_consortium_list', ["INRG"]) 

2)  Fence
    in tests_endpoints/endpoints.conftest there are two pytest fixtures that simulate calls to fence

    when creating a new test pass fence_get_users_mock as a parameter to the test function and then use side_effect=fence_get_users_mock to patch fence_get_users

    this will use the fixture fence_users to represent the fence DB

    if a test requires adding a user to fence_users mid way through a test pass fence_users as a parameter in the test function and then new users can be appended at any point

3) Arborist

    for every request add the header "Authorization": 'bearer {fence_id}'

    this will use the fence_get_users_mock to retrieve the fence user with the given fence_id

    if check_arborist_auth was a decorator on the requests method it allow the request thorugh if the fence_users role is admin


## test build project endpoint tests

The test_build_project file tests a group of users making a data request from start to finish
here is what is occuring in this test, feel free to add onto this as changes are made in amanuensis

USERS:
    in FENCE DB:
    user1
    user2
    user3
    admin

    in AMANUENSIS DB:
    user2
    admin

    in NEITHER:
    user4
    user5

1) user1 creates a filter set
    
    1) sends post req to /filter-sets?explorerId=1 to create a filter set

    2)  sends get req to /filter-sets?explorerId=1 to get all of their filter sets

    3) sends post req to /filter-sets/snapshot to create a snap shot of the filter set they created

    * user1 shares the filter set with user2 and user2 has user1 make a change
    
    1) user1 shares the snapshot code with user2

    2) user2 sends get req to /filter-sets/snapshot/{snapshot_response.json} to get the filterset from the snapshot

    3) user1 sends put req to /filter-sets/{id}?explorerId=1'to make the change to the filter set

2) the users are ready to make a data request and contact an admin to do so

    1) admin send get req to /admin/filter-sets/user" to retrieve the filter set from user1

    2) admin sends a post req to '/admin/projects' to create a project
        * user1, admin, user4, and user5 are added as associated users in this request all have metadata access
        * data was requested from INRG and INSTRUCT
    
    3) admin sends get req to "/admin/all_associated_user_roles" to retreve all roles 
    
    4) admin sends post req to "/admin/associated_user" to add user2 to project with data access

    5) admin sends post req to "/admin/associated_user" to add user3 to project with metadata access

    6) admin sends requests to readd user1 and user5 and nothing happens as they are already added

    7) admin sends put req to "/admin/associated_user_role" to give user1 data access
    
    8) admin sends put req to "/admin/associated_user_role" to get user3 data access

    * users decide they want to remove user3 from the project

    9) admin sends delete req to "/admin/remove_associated_user_from_project" to remove user3 from project
        *user3 active set to false and role set to metadata access in ProjectAssociatedUser table
    
    10) admin sends get req to "/admin/states" to get all the possible states

    * INRG data request was approved 

    11) admin sends post req to "/admin/projects/state" to change request state for INRG to approved

    *INSTRUCT requires revision to filter set

    12) admin sends post req to "/admin/projects/state" to change request state for INSTRUCT to revision

    13)  admin sends a post req to "/admin/filter-sets" to create a new filter set with corrections

    14) admin sends post req to "admin/copy-search-to-user" to add user1 to the new filter set

    15) admin sends post req to "admin/copy-search-to-project" to add the new filter set to the project

    16) admin sends post req to "/admin/projects/state" to change INSTRUCT to approved

    17) admin sends put req to "/admin/projects" to add an approved url

    18) admin sends post req to "/admin/projects/state" to move all requests to data available

    19)  user2 sends get req to "/download-urls/{project_id}" to get the data

    20) user3 sends get req to "/download-urls/{project_id}" to get the data but a 403 is returned becuase they were removed from the project

    21) admin sends get req to "/download-urls/{project_id}" to get the data but a 403 is returned becuase they dont have data access

    22) user5 signs up in fence and sends get req to /projects and their userid should be updated in the associated_users table

    23) user3 sends get reqeust to /projects and should see nothing becuase they are not an active user of the project

    24) user1 sends get req to /projects and should see the the project


    25) user1 sends get req to "filter-sets/{id}?explorerId=1" to retrieve the original filter set of the project

    26) user1 send delete req to "filter-sets/{id}?explorerId=1" to delete the oringial filter set

3) admin creates a project for user4

    1) admin sends post req to /admin/projects to create a data request

        user4 should not be added to associated_user table again



    
