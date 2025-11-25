def find_gen3_helm_path():
    # Try relative path first (most common case)
    relative_path = os.path.join(os.path.dirname(__file__), '..', 'gen3-helm')
    if os.path.exists(os.path.join(relative_path, 'helm', 'amanuensis')):
        return relative_path
    
    # Search in parent directories
    current_dir = os.path.dirname(__file__)
    for _ in range(3):  # Search up to 3 levels up
        current_dir = os.path.dirname(current_dir)
        gen3_helm_candidate = os.path.join(current_dir, 'gen3-helm')
        if os.path.exists(os.path.join(gen3_helm_candidate, 'helm', 'amanuensis')):
            return gen3_helm_candidate
    
    # Fallback to environment variable or error
    env_path = os.getenv('GEN3_HELM_PATH')
    if env_path and os.path.exists(env_path):
        return env_path
    
    fail("Could not find gen3-helm repository. Please set GEN3_HELM_PATH environment variable.")
    
custom_build(
    'amanuensis',  # Use localhost prefix for local registry
    'nerdctl --namespace k8s.io build -f Dockerfile.tilt -t $EXPECTED_REF .',  # Use nerdctl for Rancher Desktop
    deps=['./amanuensis', './Dockerfile.tilt'],  # Watch these directories/files for changes
    disable_push=True,  # Don't push to external registry - keep it local
    skips_local_docker=True,  # We are using local docker/nerdctl
    live_update=[
        # Sync local files to the container
        sync('./amanuensis', '/amanuensis/amanuensis'),
        # Restart the Flask server when files change
        run('cd /amanuensis && touch /tmp/restart.txt', trigger=['./amanuensis'])
    ]
)


# Find gen3-helm relative to current directory
gen3_helm_path = find_gen3_helm_path()

local_resource(
    'helm-common-deps',
    'cd %s/helm/common && helm dependency update' % gen3_helm_path,
    deps=[
        '%s/helm/common/Chart.yaml' % gen3_helm_path,
    ]
)

local_resource(
    'helm-deps',
    'cd %s/helm/amanuensis && helm dependency update' % gen3_helm_path,
    deps=[
        '%s/helm/amanuensis/Chart.yaml' % gen3_helm_path,
    ]
)

k8s_yaml(helm(
    '%s/helm/amanuensis' % gen3_helm_path,
    name='amanuensis',
    values=['%s/values.yaml' % gen3_helm_path],
    set=[
        "image.repository=amanuensis",
        "image.pullPolicy=Never",
        "postgres.database=amanuensis_pcdc",
        "postgres.username=amanuensis_pcdc",
        "postgres.host=pcdc-postgresql",
        "postgres.password=amanuensis_thisisaweakpassword",
        "command=null",
        "args=null",

    ]
))