FROM openmetadata/ingestion:1.3.3

# Let's use the same workdir as the ingestion image
WORKDIR /ingestion
USER airflow

# Install our custom connector
COPY connector connector
COPY setup.py .
RUN pip install requests
RUN pip install --no-deps .