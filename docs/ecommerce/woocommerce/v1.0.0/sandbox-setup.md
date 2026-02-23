# WooCommerce Sandbox Setup

## Option 1: Local WordPress + WooCommerce (Recommended for Development)

### Using Docker

```bash
# Start WordPress + MySQL locally
docker run -d --name woo-mysql \
  -e MYSQL_ROOT_PASSWORD=root \
  -e MYSQL_DATABASE=wordpress \
  mysql:8.0

docker run -d --name woo-wordpress \
  --link woo-mysql:mysql \
  -p 8080:80 \
  -e WORDPRESS_DB_HOST=mysql \
  -e WORDPRESS_DB_USER=root \
  -e WORDPRESS_DB_PASSWORD=root \
  -e WORDPRESS_DB_NAME=wordpress \
  wordpress:latest
```

### Setup Steps

1. Open `http://localhost:8080` and complete WordPress installation
2. Go to **Plugins → Add New** and install **WooCommerce**
3. Complete the WooCommerce setup wizard
4. Go to **WooCommerce → Settings → Advanced → REST API**
5. Click **Add Key**, set permissions to **Read/Write**, generate key
6. Save `Consumer Key` and `Consumer Secret`

### Add Test Data

Install WooCommerce sample data:
1. Go to **WooCommerce → Settings → Advanced → REST API**
2. Or import sample products via **Tools → Import → WooCommerce products (CSV)**

## Option 2: WooCommerce.com Sandbox

WooCommerce does not provide an official sandbox environment. Use a staging/development WordPress instance instead.

## Option 3: Mock Server

For CI/CD testing without a real WooCommerce instance, use `pytest-httpx` or `respx` to mock the WooCommerce REST API responses.

See `tests/conftest.py` for mock fixtures.

## Configuration for Sandbox

```yaml
# config/accounts.yaml
accounts:
  - name: local-dev
    store_url: "http://localhost:8080"
    consumer_key: "ck_your_generated_key"
    consumer_secret: "cs_your_generated_secret"
    api_version: "wc/v3"
    verify_ssl: false
    environment: development
```

Note: For HTTP connections (non-SSL), the connector automatically uses OAuth 1.0a authentication instead of Basic Auth.
