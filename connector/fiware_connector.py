import requests
from pathlib import Path
from typing import Iterable, Optional, List, Any
from re import sub

from metadata.ingestion.api.common import Entity
from metadata.ingestion.api.models import Either
from metadata.ingestion.api.steps import Source, InvalidSourceException
from metadata.generated.schema.entity.services.connections.metadata.openMetadataConnection import (
    OpenMetadataConnection,
)
from metadata.generated.schema.entity.services.connections.database.customDatabaseConnection import (
    CustomDatabaseConnection,
)
from metadata.generated.schema.entity.data.database import Database
from metadata.generated.schema.entity.data.databaseSchema import DatabaseSchema
from metadata.generated.schema.api.data.createDatabaseSchema import (
    CreateDatabaseSchemaRequest,
)
from metadata.generated.schema.api.data.createDatabase import CreateDatabaseRequest
from metadata.generated.schema.entity.services.databaseService import (
    DatabaseService,
)
from metadata.generated.schema.entity.data.table import (
    Column,
)
from metadata.generated.schema.metadataIngestion.workflow import (
    Source as WorkflowSource,
)
from metadata.generated.schema.api.data.createTable import CreateTableRequest
from metadata.ingestion.ometa.ometa_api import OpenMetadata
from metadata.utils.logger import ingestion_logger

logger = ingestion_logger()

class InvalidFiwareConnectorException(Exception):
    """
    Sample data is not valid to be ingested
    """

class FiwareConnector(Source):
    """
    Custom connector to ingest Database metadata from various formats.
    """
    def __init__(self, config: WorkflowSource, metadata: OpenMetadata):
        self.config = config
        self.metadata = metadata

        self.service_connection = config.serviceConnection.__root__.config
        self.broker_url: str = self.service_connection.connectionOptions.__root__.get("broker_url")
        self.database_name: str = self.service_connection.connectionOptions.__root__.get("database_name")
        self.schema_name: str = self.service_connection.connectionOptions.__root__.get("schema_name")
        self.fiware_service: str = self.service_connection.connectionOptions.__root__.get("fiware_service")
        self.fiware_service_path: str = self.service_connection.connectionOptions.__root__.get("fiware_service_path")

        if not self.broker_url:
            raise InvalidFiwareConnectorException("Missing required connection option 'broker_url' in service connection.")
        if not self.database_name and not self.fiware_service:
            raise InvalidFiwareConnectorException("Missing required connection option 'database_name' or 'fiware_service' in service connection.")
        if not self.schema_name and not self.fiware_service_path:
            raise InvalidFiwareConnectorException("Missing required connector option 'schema_name' or 'fiware_service_path' in service connection.")

        if not self.fiware_service:
            self.database = self.database_name
        else:
            self.database = self.fiware_service
        
        if not self.fiware_service_path:
            self.schema = self.schema_name
        else:
            self.schema = self.fiware_service_path
    
        self.data: Optional[List[Any]] = None
        super().__init__()

    @classmethod
    def create(
        cls, config_dict: dict, metadata_config: OpenMetadataConnection
    ) -> "FiwareConnector":
        config: WorkflowSource = WorkflowSource.parse_obj(config_dict)
        connection: CustomDatabaseConnection = config.serviceConnection.__root__.config
        if not isinstance(connection, CustomDatabaseConnection):
            raise InvalidSourceException(
                f"Expected CustomDatabaseConnection, but got {connection}"
            )
        return cls(config, metadata_config)

    def prepare(self):
        headers = {
            'Accept': 'application/json',
        }
        
        if self.fiware_service:
            headers = headers + {'Fiware-Service': self.fiware_service}
        if self.fiware_service_path:
            headers = headers + {'Fiware-ServicePath': self.fiware_service_path}
        self.data = self.query_context_broker(self.broker_url, headers)

    def query_context_broker(self, base_url, headers):
        data = []
        query_url = base_url + "/v2/types"
        try:
            response = requests.get(query_url, headers=headers)
            data = response.json()
            logger.info(f"DATA: {data}")
        except Exception as e:
            logger.error(f"Error querying context broker on {base_url}: {e}")
            raise InvalidFiwareConnectorException(f"Error querying context broker on {base_url}: {e}")
    
        return data

    def yield_create_request_database_service(self):
        yield Either(
            right=self.metadata.get_create_service_from_source(
                entity=DatabaseService, config=self.config
            )
        )

    def yield_db_name(self):
        # Pick up the service we just created (if not UI)
        service_entity: DatabaseService = self.metadata.get_by_name(
                entity=DatabaseService, fqn=self.config.serviceName
            )

        yield Either(
            right=CreateDatabaseRequest(
                name=self.database,
                service=service_entity.fullyQualifiedName,
            )
        )

    def yield_schema(self):
        # Pick up the service we just created (if not UI)
        database_entity: Database = self.metadata.get_by_name(
            entity=Database, fqn=f"{self.config.serviceName}.{self.database}"
        )

        yield Either(
            right=CreateDatabaseSchemaRequest(
                name=self.schema,
                database=database_entity.fullyQualifiedName,
            )
        )

    def yield_data(self):
        """
        Iterate over the data list to create tables
        """
        database_schema: DatabaseSchema = self.metadata.get_by_name(
            entity=DatabaseSchema,
            fqn=f"{self.config.serviceName}.{self.database_name}.{self.schema}",
        )

        for type in self.data:
            yield Either(
                right=CreateTableRequest(
                    name=type['type'],
                    databaseSchema=database_schema.fullyQualifiedName,
                    columns=[
                        Column(
                            name=key,
                            dataType=self.map_datatypes(key, type['attrs']),
                            description=type['attrs'][key]['types'][0],
                        )
                        for key in type['attrs'].keys()
                    ],
                )
            )
         
    def map_datatypes(self, key, datatype):
        if key == 'location':
            return 'JSON'
        elif 'int' in datatype:
            return 'INT'
        elif 'float' in datatype:
            return 'FLOAT'
        elif 'str' in datatype:
            return 'STRING'
        else:
            return 'NULL'
        
    def _iter(self) -> Iterable[Entity]:
        yield from self.yield_create_request_database_service()
        yield from self.yield_db_name()
        yield from self.yield_schema()
        yield from self.yield_data()

    def test_connection(self) -> None:
        pass

    def close(self):
        pass
