# Cryptocurrency Wallet Microservices

A production-ready microservices architecture for cryptocurrency wallet management and user verification, built with FastAPI, PostgreSQL, and Apache Kafka.

## 🏗️ Architecture

The system consists of two main microservices:

- **User Verification Service** (Port 8000) - Handles document verification and user validation
- **Wallet Service** (Port 8001) - Manages cryptocurrency wallet generation and retrieval

### Event-Driven Communication

Services communicate through Apache Kafka using event-driven patterns:
- User verification completion triggers automatic wallet creation
- Asynchronous processing ensures high availability and scalability

## 🚀 Features

### User Verification Service
- **Document Processing**: Upload and verify identity documents (JPG, PNG, PDF)
- **Multi-Network Support**: Ethereum, Bitcoin, Tron blockchain networks
- **Async Verification**: Non-blocking document processing with configurable delays
- **Event Publishing**: Publishes `user.verified` events to Kafka
- **Comprehensive Testing**: 95%+ test coverage with pytest

### Wallet Service
- **HD Wallet Generation**: Hierarchical deterministic wallets using BIP-44 standard
- **Multi-Blockchain**: Support for Ethereum, Bitcoin, and Tron
- **Event-Driven**: Automatically creates wallets when users are verified
- **Caching Layer**: In-memory caching for improved performance
- **Security**: Mnemonic encryption and secure seed derivation

## 🛠️ Technology Stack

- **Framework**: FastAPI (Python 3.12)
- **Database**: PostgreSQL 15 with async SQLAlchemy
- **Message Broker**: Apache Kafka with Zookeeper
- **Caching**: In-memory cache service
- **Containerization**: Docker & Docker Compose
- **Testing**: pytest with comprehensive test suites
- **Code Quality**: Ruff linter and formatter

## 📋 Prerequisites

- Docker and Docker Compose
- Python 3.12+ (for local development)
- Make (optional, for using Makefile commands)

## 🚀 Quick Start

### Using Docker Compose (Recommended)

1. **Clone and start services**:
```bash
git clone <repository-url>
cd <project-directory>
docker-compose up -d
```

2. **Verify services are running**:
```bash
# Check service health
curl http://localhost:8000/health  # User Verification Service
curl http://localhost:8001/health  # Wallet Service

# Access Kafka UI
open http://localhost:8080
```

### Local Development

1. **Set up environment**:
```bash
make dev-setup  # Creates venv and installs dependencies
source .venv/bin/activate
```

2. **Start infrastructure**:
```bash
docker-compose up -d postgres kafka zookeeper kafka-ui
```

3. **Configure environment variables**:
```bash
export DATABASE_URL="postgresql+asyncpg://postgres:password@localhost:5432/user_verification_db"
export KAFKA_BOOTSTRAP_SERVERS="localhost:9092"
export MNEMONIC="your-secure-mnemonic-phrase-here"
```

4. **Run services**:
```bash
# Terminal 1 - User Verification Service
cd user_verification_service
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# Terminal 2 - Wallet Service  
cd wallet_service
uvicorn main:app --host 0.0.0.0 --port 8001 --reload
```

## 📚 API Documentation

### User Verification Service (Port 8000)

**Verify User Document**
```bash
POST /verify
Content-Type: application/json

{
  "user_id": "user123",
  "network": "ethereum",
  "document": "base64-encoded-document"
}
```

**Health Check**
```bash
GET /health
```

### Wallet Service (Port 8001)

**Get User Wallet**
```bash
GET /wallet/{user_id}?network=ethereum
```

**Health Check**
```bash
GET /health
```

### Interactive API Documentation
- User Verification: http://localhost:8000/api/docs
- Wallet Service: http://localhost:8001/api/docs

## 🔧 Configuration

### Environment Variables

**User Verification Service**:
```bash
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/user_verification_db
KAFKA_BOOTSTRAP_SERVERS=localhost:9092
MAX_DOCUMENT_SIZE_MB=10
VERIFICATION_DELAY_SECONDS=3.0
```

**Wallet Service**:
```bash
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/wallet_service_db
KAFKA_BOOTSTRAP_SERVERS=localhost:9092
MNEMONIC=your-secure-mnemonic-phrase
MAX_CONCURRENT_GENERATIONS=50
```

## 🧪 Testing

### Run All Tests
```bash
make test                    # Run all tests
make test-cov               # Run with coverage report
```

### Service-Specific Tests
```bash
# User Verification Service
cd user_verification_service
python -m pytest tests/ -v

# Wallet Service  
cd wallet_service
python -m pytest tests/ -v
```

### Test Coverage
The project maintains high test coverage:
- Repository layer: 100%
- Service layer: 95%+
- API endpoints: 90%+

## 🔒 Security Features

- **Mnemonic Encryption**: Support for encrypted mnemonic storage
- **Secure Seed Derivation**: User-specific entropy for wallet generation
- **Input Validation**: Comprehensive request validation and sanitization
- **Error Handling**: Secure error responses without information leakage
- **Rate Limiting**: Configurable concurrency limits

## 📊 Monitoring & Observability

- **Structured Logging**: JSON-formatted logs with request tracing
- **Health Endpoints**: Comprehensive health checks for all dependencies
- **Kafka UI**: Web interface for monitoring message queues
- **Request Tracing**: Unique request IDs for distributed tracing

## 🛠️ Development Tools

### Code Quality
```bash
make lint                   # Run linter
make format                 # Format code
make type-check            # Type checking
make check-all             # All quality checks
```

### Database Management
```bash
make clean                 # Clean caches and temp files
make deps                  # Show dependencies
make info                  # Project information
```

## 🏗️ Project Structure

```
├── user_verification_service/     # User verification microservice
│   ├── src/
│   │   ├── api/                  # FastAPI routes and middleware
│   │   ├── core/                 # Configuration and utilities
│   │   ├── domain/               # Business logic and models
│   │   ├── infrastructure/       # Database, Kafka, repositories
│   │   └── services/             # Application services
│   └── tests/                    # Comprehensive test suite
├── wallet_service/               # Wallet management microservice
│   ├── api/                      # API layer
│   ├── core/                     # Core utilities
│   ├── domain/                   # Domain models and interfaces
│   ├── infrastructure/           # Infrastructure implementations
│   ├── services/                 # Business services
│   └── tests/                    # Test suite
├── docker-compose.yml            # Service orchestration
├── Makefile                      # Development commands
└── pyproject.toml               # Python configuration
```