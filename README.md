## Midas Core

High throughput financial transaction processing microservice built with Spring Boot,Apache Kafka,and Spring Data JPA.


## Overview

Midas Core is the central service responsible for receiving, validating, and recording financial transactions at scale. It integrates three external infrastructure components that are Apache Kafka for asynchronous ingestion, an H2 relational database for persistence, and a dedicated Incentive API for real time reward computation and exposes processed account data via a REST endpoint.



## Tech Stack

Runtime : Java (version 17)

Framework  : Springboot (version 3.2.5)

Message Quque : Apache Kafka (version 3.1.4)

Persistence : Spring Data JPA + H2 (version 2.2.224)

Build Tool : Maven  (3.x)

Testing : Testcontainers + EmbeddedKafka1.19.1


## Getting Started

####  Prerequisites

- Java 17
- Maven 3.x (or use the included mvnw wrapper)
- The Incentive API JAR (included in services/)

#### Run the Incentive API

Start the external incentive service in a separate terminal before running the application or tests:

``` bash
cd services
java -jar transaction-incentive-api.jar
```

#### Build & Run

```bash
./mvnw clean install
./mvnw spring-boot:run
```

#### Run Tests

```bash
# Full test suite
./mvnw test

# Individual task tests
./mvnw -Dtest=TaskOneTests test
./mvnw -Dtest=TaskFiveTests test

Windows: Use .\mvnw.cmd instead of ./mvnw
```

#### Configuration

All runtime configuration lives in `src/main/resources/application.yml.`

``` yaml
server:
  port: 33400

general:
  kafka-topic: trader-updates

spring:
  kafka:
    consumer:
      group-id: midas-core
      auto-offset-reset: earliest
      value-deserializer: org.springframework.kafka.support.serializer.JsonDeserializer
    producer:
      value-serializer: org.springframework.kafka.support.serializer.JsonSerializer
  jpa:
    hibernate:
      ddl-auto: create-drop
```

## API Reference

GET /balance
Returns the current balance for a given user.

```
GET http://localhost:33400/balance?userId={id}
```

Response
```
json{ "amount": 1842.50 }
```
Returns amount: 0 for unknown user IDs.


## Project Structure
``` bash
src/
├── main/java/com/jpmc/midascore/
│   ├── component/
│   │   ├── TransactionListener.java   # Kafka consumer
│   │   ├── DatabaseConduit.java       # Validation + persistence orchestration
│   │   └── IncentiveService.java      # External REST API client
│   ├── controller/
│   │   ├── BalanceController.java     # GET /balance endpoint
│   │   └── GlobalExceptionHandler.java
│   ├── entity/
│   │   ├── UserRecord.java            # JPA user entity
│   │   └── TransactionRecord.java     # JPA transaction entity (@ManyToOne)
│   ├── foundation/
│   │   ├── Transaction.java           # Kafka message DTO
│   │   ├── Balance.java               # API response DTO
│   │   └── Incentive.java             # Incentive API response DTO
│   └── repository/
│       ├── UserRepository.java
│       └── TransactionRepository.java
└── test/java/com/jpmc/midascore/
    ├── TaskOneTests.java    # Dependency & config validation
    ├── TaskTwoTests.java    # Kafka integration
    ├── TaskThreeTests.java  # Database persistence
    ├── TaskFourTests.java   # Incentive API integration
    └── TaskFiveTests.java   # REST endpoint verification

```

## Transaction Validation Rules

A transaction is accepted and persisted only if all three conditions are met:

- `senderId` resolves to an existing user
- `recipientId` resolves to an existing user
- Sender's current balance ≥ transaction amount

On acceptance — sender balance is debited, recipient balance is credited with amount + incentive. Invalid transactions are discarded with no side effects.

## Built As Part Of

JPMC Advanced Software Engineering — Forage Program

Extended version with PostgreSQL, fraud detection ML, and MLOps layer: midas-extended