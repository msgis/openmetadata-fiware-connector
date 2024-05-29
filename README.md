# OpenMetadata Fiware Connector
This repository is an custom [OpenMetadata](https://open-metadata.org/) Connector for the [FIWARE Context Broker](https://www.fiware.org/2020/12/11/fiware-context-broker-the-engine-for-future-energy-systems/).


## Step 1 - Prepare the package installation
We'll need to package the code so that it can be shipped to the ingestion container and used there. You can find a simple `setup.py` that builds the `connector` module.

## Step 2 - Prepare the Ingestion Image

If you want to use the connector from the UI, the `openmetadata-ingestion` image should be aware of your new package.

We will be running the against the OpenMetadata version `1.3.3`, therefore, our Dockerfile looks like:

```Dockerfile
# Base image from the right version
FROM openmetadata/ingestion:1.3.3

# Let's use the same workdir as the ingestion image
WORKDIR ingestion
USER airflow

# Install our custom connector
# For a PROD image, this could be picking up the package from your private package index
COPY connector connector
COPY setup.py .
RUN pip install requests
RUN pip install --no-deps .
```
Build and use the new openmetadata-ingestion images in Docker compose:
```yaml
  ingestion:
    container_name: openmetadata_ingestion
    build:
      context: ../
      dockerfile: docker/Dockerfile
```

## Step 3 - Run OpenMetadata with the custom Ingestion image

We have a `Makefile` prepared for you to run `make run`. This will get OpenMetadata up in Docker Compose using the custom Ingestion image.

You may also just run:

```cmd
docker compose -f ./docker/docker-compose.yml up -d
```

## Step 4 - Configure the Connector

In this guide we prepared a Database Connector. Thus, go to `Database Services > Add New Service > Custom` and set the `Source Python Class Name` as `connector.fiware_connector.FiwareConnector`.

Note how we are specifying the full module name so that the Ingestion Framework can import the Source class.

![demo.gif](images%2Fsetup_demo.gif)

## OpenMetadata Fiware Connector

To run the OpenMetadata Fiware Connector, the Python class will be `connector.fiware_connector.FiwareConnector` and we'll need to set the following Connection Options:
- `broker_url`: The base URL to of the Fiware Conetxt Broker.
- `database_name`: Any name you'd like - preferably no special characters.
- `schema_name`: Any name you'd like - preferably no special characters.
- `fiware_service`: Used to specify the Fiware service/tenant, when Muti Tenancy is enabled. Optional - if used given overrides `database_name`. (Read more about [Multi Tenacy](https://fiware-orion.readthedocs.io/en/master/orion-api.html#multi-tenancy).)
- `fiware_service_path`: Used to specify the hierarchical scopes. Optional - if used given overrides `schema_name`. (Read more about [Hierarchical Scopes](https://fiware-orion.readthedocs.io/en/master/orion-api.html#service-path).) This option is currently untested. Issues with `/` used in service-paths could occur.

## Contributing

Everyone is invited to get involved and contribute to the project.

Simply create a [fork and pull request](https://docs.github.com/en/get-started/quickstart/contributing-to-projects) for code contributions or
feel free to [open an issue](https://github.com/msgis/openmetadata-fiware-connector/issues) for any other contributions or issues.