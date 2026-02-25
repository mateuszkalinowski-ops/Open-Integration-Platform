"""Configuration for InsERT Nexo on-premise agent — loaded from environment variables."""

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_config = {"env_prefix": "NEXO_AGENT_", "env_nested_delimiter": "__"}

    app_name: str = "insert-nexo-agent"
    app_version: str = "1.0.0"
    agent_id: str = Field(default="nexo-agent-001", alias="NEXO_AGENT_ID")
    debug: bool = False

    host: str = "0.0.0.0"
    port: int = 8000
    log_level: str = "INFO"

    sql_server: str = Field(default=r"(local)\INSERTNEXO", alias="NEXO_SQL_SERVER")
    sql_database: str = Field(default="Nexo_demo", alias="NEXO_SQL_DATABASE")
    sql_auth_windows: bool = Field(default=True, alias="NEXO_SQL_AUTH_WINDOWS")
    sql_username: str = Field(default="", alias="NEXO_SQL_USERNAME")
    sql_password: str = Field(default="", alias="NEXO_SQL_PASSWORD")

    nexo_operator_login: str = Field(default="", alias="NEXO_OPERATOR_LOGIN")
    nexo_operator_password: str = Field(default="", alias="NEXO_OPERATOR_PASSWORD")
    nexo_product: str = Field(default="Subiekt", alias="NEXO_PRODUCT")

    sdk_bin_path: str = Field(
        default=r"C:\nexoSDK\Bin",
        alias="NEXO_SDK_BIN_PATH",
    )

    default_warehouse: str = "MAG"
    default_branch: str = "CENTRALA"

    cloud_platform_url: str = Field(
        default="https://integrations.pinquark.com",
        alias="CLOUD_PLATFORM_URL",
    )
    cloud_api_key: str = Field(default="", alias="CLOUD_API_KEY")

    heartbeat_interval_seconds: int = 60
    sync_interval_seconds: int = 300
    sync_batch_size: int = 100

    offline_queue_db: str = Field(
        default="nexo_agent_queue.db",
        alias="NEXO_QUEUE_DB",
    )

    erp_ping_interval_seconds: int = 30
    erp_ping_warning_threshold: int = 3
    erp_ping_critical_threshold: int = 10

    kafka_enabled: bool = Field(default=False, alias="KAFKA_ENABLED")
    kafka_bootstrap_servers: str = Field(
        default="localhost:9092",
        alias="KAFKA_BOOTSTRAP_SERVERS",
    )
    kafka_security_protocol: str = Field(default="PLAINTEXT", alias="KAFKA_SECURITY_PROTOCOL")
    kafka_sasl_mechanism: str = Field(default="PLAIN", alias="KAFKA_SASL_MECHANISM")
    kafka_sasl_username: str = Field(default="", alias="KAFKA_SASL_USERNAME")
    kafka_sasl_password: str = Field(default="", alias="KAFKA_SASL_PASSWORD")

    kafka_topic_contractors: str = "insert-nexo.output.erp.contractors.sync"
    kafka_topic_products: str = "insert-nexo.output.erp.products.sync"
    kafka_topic_documents: str = "insert-nexo.output.erp.documents.sync"
    kafka_topic_orders: str = "insert-nexo.output.erp.orders.sync"
    kafka_topic_stock: str = "insert-nexo.output.erp.stock.sync"


settings = Settings()
