# pylint: disable=redefined-outer-name

import os
import time
from unittest import mock

import pytest

import docker
from zetta_utils.layer.db_layer.datastore import DatastoreBackend, build_datastore_layer


@pytest.fixture(scope="session")
def datastore_emulator():
    """Ensure that the DataStore service is up and responsive."""

    client = docker.from_env()
    project = "test-project"
    options = "--no-store-on-disk --consistency=1.0 --host-port=0.0.0.0:8081"
    command = f"gcloud --project {project} beta emulators datastore start {options}"

    container = client.containers.run(
        "motemen/datastore-emulator:alpine",
        command=command,
        detach=True,
        remove=True,
        # ports={"8081": "8081"},
        network_mode="host",
    )

    timeout = 120
    stop_time = 1
    elapsed_time = 0
    while container.status != "running" and elapsed_time < timeout:
        time.sleep(stop_time)
        elapsed_time += stop_time
        try:
            container.reload()
        except docker.errors.DockerException:
            break

    if container.status != "running":
        raise RuntimeError(f"Container failed to start: {container.logs()}")

    time.sleep(2)  # wait for emulator to boot

    endpoint = "localhost:8081"

    environment = {}
    environment["DATASTORE_EMULATOR_HOST"] = endpoint
    environment["DATASTORE_DATASET"] = project
    environment["DATASTORE_EMULATOR_HOST_PATH"] = "localhost:8081/datastore"
    environment["DATASTORE_HOST"] = f"http://{endpoint}"
    environment["DATASTORE_PROJECT_ID"] = project

    with mock.patch.dict(os.environ, environment):
        yield project

    container.kill()
    time.sleep(0.2)


def test_build_layer(datastore_emulator):
    layer = build_datastore_layer(datastore_emulator, datastore_emulator)
    assert isinstance(layer.backend, DatastoreBackend)


def test_write_scalar(datastore_emulator) -> None:
    layer = build_datastore_layer(datastore_emulator, datastore_emulator)
    layer["key"] = "val"
    assert layer["key"] == "val"
