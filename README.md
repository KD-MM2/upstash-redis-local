# Redis REST API Wrapper

This project provides a REST API wrapper for a local Redis instance, making it compatible with the [Upstash Redis REST API](https://docs.upstash.com/redis/features/restapi). It allows you to interact with a local Redis database using HTTP requests, emulating the behavior of Upstash's REST API.

## Features

- **Upstash REST API Compatibility**: Supports commands like `GET`, `SET`, `MGET`, `ZADD`, and more, following the same URL path and parameter conventions as Upstash.
- **Pipelining**: Execute multiple Redis commands in a single HTTP request using the `/pipeline` endpoint.
- **Transactions**: Execute atomic transactions using the `/multi-exec` endpoint.
- **Pub/Sub**: Supports Redis publish/subscribe functionality via `/publish` and `/subscribe` endpoints.
- **Monitor**: Real-time monitoring of Redis commands using the `/monitor` endpoint with Server-Sent Events (SSE).
- **Response Formats**: Supports JSON and RESP2 response formats, as well as Base64 encoding for binary data.

## Prerequisites

- Python 3.12
- Redis server (local or remote)

## Installation

### Direct

1. Initial virtual environment:

   ```bash
   python -m venv .venv

   # Windows
   .\.venv\scripts\activate.ps1

   # Linux
   . ./src/bin/activate
   ```

2. Prepair env file:

   - Create a .env file in the project directory with the following content and adjust the values as needed:

   ```bash
   REDIS_HOST=<REDIS_HOST(eg: 127.0.0.1 or localhost)>
   REDIS_PORT=<REDIS_PORT(eg: 6379)>
   REDIS_DB=0
   SERVER_HOST=<SERVER_HOST(eg: 127.0.0.1 or localhost)>
   SERVER_PORT=<SERVER_PORT(eg: 8000)>
   WORKER_COUNT=<WORKER_COUNT(eg: 2)>
   HOST_PORT=<HOST_PORT(eg: 8000)> # Only needed for docker
   ```

3. Install dependencies:

   ```bash
   # Change version with the latest version
   pip install upstash_redis_local-<VERSION>-cp312-cp312-linux_x86_64.whl
   ```

4. Start the Redis server (if not already running):
   ```bash
   python -m upstash_redis_local
   ```

### Docker Compose (Recommended)

1. Prepair env file:

   - Create a .env file in the project directory with the following content and adjust the values as needed:

   ```bash
   REDIS_HOST=<REDIS_HOST(eg: 127.0.0.1 or localhost)>
   REDIS_PORT=<REDIS_PORT(eg: 6379)>
   REDIS_DB=0
   SERVER_HOST=<SERVER_HOST(eg: 127.0.0.1 or localhost)>
   SERVER_PORT=<SERVER_PORT(eg: 8000)>
   WORKER_COUNT=<WORKER_COUNT(eg: 2)>
   HOST_PORT=<HOST_PORT(eg: 8000)> # Only needed for docker
   ```

2. Start the Container:
   ```bash
   docker compose up -d --build
   ```

The API will be available at `http://localhost:8000`.

## Usage

### Basic Commands

#### Set a Key

```bash
curl -X POST http://localhost:8000/SET/foo/bar -H "Authorization: Bearer dummy_token"
# Response: {"result":"OK"}
```

#### Get a Key

```bash
curl http://localhost:8000/GET/foo -H "Authorization: Bearer dummy_token"
# Response: {"result":"bar"}
```

### Pipelining

Send multiple commands in a single request:

```bash
curl -X POST http://localhost:8000/pipeline -H "Authorization: Bearer dummy_token" -d '[
  ["SET", "key1", "value1"],
  ["GET", "key1"]
]'
# Response: [{"result":"OK"}, {"result":"value1"}]
```

### Transactions

Execute atomic transactions:

```bash
curl -X POST http://localhost:8000/multi-exec -H "Authorization: Bearer dummy_token" -d '[
  ["SET", "key1", "value1"],
  ["INCR", "counter"]
]'
# Response: [{"result":"OK"}, {"result":1}]
```

### Pub/Sub

#### Subscribe to a Channel

```bash
curl -X POST http://localhost:8000/subscribe/chat -H "Authorization: Bearer dummy_token" -H "Accept:text/event-stream"
```

#### Publish to a Channel

```bash
curl -X POST http://localhost:8000/publish/chat/hello -H "Authorization: Bearer dummy_token"
# Response: {"result":1} (number of subscribers)
```

### Monitor Redis Commands

Monitor all Redis commands in real-time:

```bash
curl -X POST http://localhost:8000/monitor -H "Authorization: Bearer dummy_token" -H "Accept:text/event-stream"
```

### Response Encoding

#### Base64 Encoding

```bash
curl http://localhost:8000/GET/foo -H "Authorization: Bearer dummy_token" -H "Upstash-Encoding: base64"
# Response: {"result":"YmFy"} (Base64 encoded "bar")
```

#### RESP2 Format

```bash
curl http://localhost:8000/GET/foo -H "Authorization: Bearer dummy_token" -H "Upstash-Response-Format: resp2"
# Response: $3\r\nbar\r\n
```

## Configuration

### Environment Variables

- `REDIS_HOST`: Redis server host (default: `localhost`).
- `REDIS_PORT`: Redis server port (default: `6379`).
- `API_PORT`: Port for the REST API (default: `8000`).

Set these variables in a `.env` file or directly in your environment.

### Authentication

The wrapper uses a mock token validation system. Replace `dummy_token` with your actual token validation logic if needed.

## Limitations

- **Blocking Commands**: Commands like `BLPOP`, `BRPOP`, and `BZPOPMAX` are not supported.
- **Cluster Mode**: Redis cluster mode is not supported.
- **Performance**: This wrapper is not optimized for high-throughput production use.

## Contributing

Contributions are welcome! Please open an issue or submit a pull request for any improvements or bug fixes.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
