###########
Development
###########


*******
Sandbox
*******

Acquire sources, create Python virtualenv, install package and dependencies,
and run software tests::

    git clone https://github.com/daq-tools/influxio
    cd influxio
    python3 -m venv .venv
    source .venv/bin/activate
    pip install --use-pep517 --prefer-binary --editable=.[test,develop,release]

    # Run linter and regular test suite.
    poe check


****************
Build OCI images
****************

OCI images will be automatically published to the GitHub Container Registry
(GHCR), see `influxio packages on GHCR`_. If you want to build images on your
machine, you can use those commands::

    export DOCKER_BUILDKIT=1
    export COMPOSE_DOCKER_CLI_BUILD=1
    export BUILDKIT_PROGRESS=plain
    docker build --tag local/influxio --file release/oci/Dockerfile .

::

    docker run --rm -it local/influxio influxio --version
    docker run --rm -it local/influxio influxio info


.. _influxio packages on GHCR: https://github.com/orgs/daq-tools/packages?repo_name=influxio
