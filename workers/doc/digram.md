Based on your Redis Streams worker implementation, here are the **Composite Structure Diagram** and **Behavior Diagrams**:

# Composite Structure Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                             SyncWorker System                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────┐    ┌─────────────────────────────────────────────┐     │
│  │  StreamProcessor │    │              RedisStreamsClient             │     │
│  │                 │    │                                             │     │
│  │ - running: bool │    │ - host: str = "redis"                       │     │
│  │ - shutdown_req: │    │ - port: int = 6379                          │     │
│  │   bool          │    │ - decode_responses: bool = False            │     │
│  │ - cleanup_hand- │    │ - socket_timeout: int = 5                   │     │
│  │   lers: List    │    │                                             │     │
│  │ - retry_config: │    │ + xreadgroup()                              │     │
│  │   RetryConfig   │    │ + xautoclaim()                              │     │
│  │                 │    │ + xack()                                    │     │
│  │ + should_conti- │    │ + xadd()                                    │     │
│  │   nue() → bool  │    │ + setnx()                                   │     │
│  │ + calculate_re- │    │ + expire()                                  │     │
│  │   try_delay()   │    │                                             │     │
│  └─────────────────┘    └─────────────────────────────────────────────┘     │
│          ▲                         ▲                                        │
│          │                         │                                        │
│          │                         │                                        │
│  ┌───────┴─────────────────────────┴────────┐    ┌─────────────────────┐    │
│  │             SyncWorker                   │    │     SyncService      │    │
│  │                                          │    │                     │    │
│  │ - retry_config: RetryConfig              │    │ - embed_client:      │    │
│  │ - processor: StreamProcessor             │    │   BaseEmbedClient    │    │
│  │ - svc: SyncService                       │    │ - chroma: Chroma-    │    │
│  │                                          │    │   Client             │    │
│  │ + ensure_group()                         │    │ - redis: RedisClient │    │
│  │ + drain_pending()                        │    │                     │    │
│  │ + process_stream()                       │    │ + handle(event)      │    │
│  │ + _process_with_retry() → bool           │    └─────────────────────┘    │
│  │ + _process_message() → ProcessingResult  │              ▲                │
│  │ + _handle_dlq()                          │              │                │
│  └──────────────────────────────────────────┘              │                │
│                             ▲                              │                │
│                             │                              │                │
│                             │                              │                │
│  ┌──────────────────────────┴──────────────────────────────┴──────────────┐ │
│  │                         External Systems                               │ │
│  │                                                                        │ │
│  │  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────┐  │ │
│  │  │  Redis      │    │  ChromaDB   │    │  Postgres   │    │  DLQ    │  │ │
│  │  │  Stream     │    │  Vector     │    │  Database   │    │ Stream  │  │ │
│  │  │ "notes:events"│  │  Store      │    │             │    │"notes:  │  │ │
│  │  │             │    │             │    │             │    │events:dlq"│  │ │
│  │  └─────────────┘    └─────────────┘    └─────────────┘    └─────────┘  │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
```

# Behavior Diagrams

## 1. Sequence Diagram - Message Processing Flow

```
┌─────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────┐
│  Redis  │    │ SyncWorker  │    │StreamProcessor│   │SyncService  │    │ Chroma  │
│ Stream  │    │             │    │              │   │             │    │         │
└────┬────┘    └──────┬──────┘    └──────┬───────┘   └──────┬──────┘    └────┬────┘
     │                 │                  │                  │                │
     │ 1. XREADGROUP   │                  │                  │                │
     │────────────────>│                  │                  │                │
     │                 │                  │                  │                │
     │ 2. Message      │                  │                  │                │
     │<────────────────│                  │                  │                │
     │                 │                  │                  │                │
     │                 │3. process_stream()│                  │                │
     │                 │─────────────────>│                  │                │
     │                 │                  │                  │                │
     │                 │4. _process_message()                 │                │
     │                 │────────────────────────────────────>│                │
     │                 │                  │                  │                │
     │                 │                  │                  │5. handle(event) │
     │                 │                  │                  │───────────────>│
     │                 │                  │                  │                │
     │                 │                  │                  │6. embed text   │
     │                 │                  │                  │───────────────>│
     │                 │                  │                  │                │
     │                 │                  │                  │7. upsert to Chroma
     │                 │                  │                  │───────────────>│
     │                 │                  │                  │                │
     │                 │                  │                  │8. Success      │
     │                 │                  │                  │<───────────────│
     │                 │                  │                  │                │
     │                 │9. XACK           │                  │                │
     │<────────────────│                  │                  │                │
     │                 │                  │                  │                │
```

## 2. State Machine Diagram - Message Lifecycle

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           Message Lifecycle                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────┐      ┌─────────────┐      ┌─────────────┐      ┌─────────┐ │
│  │   Pending   │─────>│ Processing  │─────>│  Success    │─────>│  Done   │ │
│  │ (Unacked)   │      │             │      │             │      │ (Acked) │ │
│  └─────────────┘      └─────────────┘      └─────────────┘      └─────────┘ │
│        │                     │                     │                        │
│        │                     │                     │                        │
│        ▼                     ▼                     ▼                        │
│  ┌─────────────┐      ┌─────────────┐      ┌─────────────┐                  │
│  │   Failed    │─────>│  Retrying   │      │   DLQ       │                  │
│  │ (Unacked)   │      │             │      │ (Acked)     │                  │
│  └─────────────┘      └─────────────┘      └─────────────┘                  │
│        ︎                     │                     │                        │
│        ︎                     ▼                     │                        │
│        ︎             ┌─────────────┐               │                        │
│        ︎             │ Max Retries │───────────────┘                        │
│        ︎             │ Exceeded    │                                       │
│        ︎             └─────────────┘                                       │
│        ︎                                                                    │
└─────────────────────────────────────────────────────────────────────────────┘
```

## 3. Activity Diagram - Stream Processing Workflow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        Stream Processing Workflow                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  [Start Worker]                                                             │
│        │                                                                    │
│        ▼                                                                    │
│  [Ensure Consumer Group Exists]                                             │
│        │                                                                    │
│        ▼                                                                    │
│  [Drain Pending Messages]                                                   │
│        │                                                                    │
│        ▼                                                                    │
│  ┌─────────────────┐                                                        │
│  │ For each batch: │                                                        │
│  └─────────────────┘                                                        │
│        │                                                                    │
│        ▼                                                                    │
│  [Auto-claim Stuck Messages]                                                │
│        │                                                                    │
│        ▼                                                                    │
│  [XREADGROUP for New Messages]                                              │
│        │                                                                    │
│        ▼                                                                    │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ For each message:                                                   │   │
│  │   1. Check duplicate (idempotency)                                  │   │
│  │   2. Process message via SyncService                                │   │
│  │   3. If success → XACK                                              │   │
│  │   4. If failure → retry or send to DLQ                              │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│        │                                                                    │
│        ▼                                                                    │
│  [Shutdown?] ───Yes───→ [Execute Cleanup] ───→ [Stop]                       │
│        │No                                                                  │
│        ▼                                                                    │
│  [Continue Loop]                                                            │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

## 4. Component Interaction Overview

```
┌───────────────────────┐    ┌───────────────────────┐    ┌───────────────────────┐
│      API Service      │    │     Redis Stream      │    │     SyncWorker        │
│                       │    │                       │    │                       │
│  ┌─────────────────┐  │    │  ┌─────────────────┐  │    │  ┌─────────────────┐  │
│  │   emit_event()  │──┼────┼─>│  XADD to stream │  │    │  │ XREADGROUP      │  │
│  └─────────────────┘  │    │  └─────────────────┘  │    │  │ processing      │  │
│                       │    │                       │    │  └─────────────────┘  │
└───────────────────────┘    └───────────────────────┘    │           │           │
                                                          │           ▼           │
┌───────────────────────┐    ┌───────────────────────┐    │  ┌─────────────────┐  │
│      Database         │    │      ChromaDB         │    │  │  SyncService    │──┼─┐
│                       │    │                       │    │  │                 │  │ │
│  ┌─────────────────┐  │    │  ┌─────────────────┐  │    │  │  handle(event)  │──┼─┼─>┐
│  │   Note CRUD     │  │    │  │   Vector        │<─┼────┼──│                 │  │ │  │
│  └─────────────────┘  │    │  │   Operations    │  │    │  └─────────────────┘  │ │  │
│                       │    │  └─────────────────┘  │    │                       │ │  │
└───────────────────────┘    └───────────────────────┘    └───────────────────────┘ │  │
                                                                                    │  │
┌───────────────────────┐    ┌───────────────────────┐                              │  │
│      Dead Letter      │    │     Retry Mechanism   │                              │  │
│         Queue         │    │                       │                              │  │
│                       │    │  ┌─────────────────┐  │                              │  │
│  ┌─────────────────┐  │    │  │  Exponential   │  │                              │  │
│  │   XADD to DLQ   │<─┼────┼──│   Backoff      │<─┼──────────────────────────────┘  │
│  └─────────────────┘  │    │  └─────────────────┘  │                                │
│                       │    │                       │                                │
└───────────────────────┘    └───────────────────────┘                                │
                                                                                      │
┌───────────────────────┐                                                            │
│     Signal Handling   │                                                            │
│                       │                                                            │
│  ┌─────────────────┐  │                                                            │
│  │  Graceful       │  │                                                            │
│  │  Shutdown       │<─┼────────────────────────────────────────────────────────────┘
│  └─────────────────┘  │
│                       │
└───────────────────────┘
```

## Key Architectural Features:

1. **At-Least-Once Delivery**: XREADGROUP + XACK pattern ensures messages are processed at least once
2. **Idempotency**: Duplicate detection using Redis SETNX
3. **Dead Letter Queue**: Failed messages after max retries go to DLQ
4. **Exponential Backoff**: Smart retry mechanism for transient failures
5. **Graceful Shutdown**: Signal handling for clean termination
6. **Consumer Group**: Multiple workers can load balance
7. **Auto-Claim**: Stuck messages are automatically reclaimed from other consumers

This architecture provides production-grade reliability for your stream processing system!

---

Here are the **Mermaid.js diagrams** for your Redis Streams worker system:

## 1. Composite Structure Diagram

```mermaid
classDiagram
    class SyncWorkerSystem {
        -StreamProcessor processor
        -RedisStreamsClient redisClient
        -SyncService syncService
    }

    class StreamProcessor {
        +bool running
        +bool shutdown_requested
        +List cleanup_handlers
        +RetryConfig retry_config
        +should_continue() bool
        +calculate_retry_delay() int
    }

    class RedisStreamsClient {
        +string host = "redis"
        +int port = 6379
        +bool decode_responses = false
        +xreadgroup()
        +xautoclaim()
        +xack()
        +xadd()
        +setnx()
        +expire()
    }

    class SyncService {
        +BaseEmbedClient embed_client
        +ChromaClient chroma
        +RedisClient redis
        +handle(event)
    }

    class ExternalSystems {
        +RedisStream notes_events
        +ChromaDB vector_store
        +Postgres database
        +DLQStream notes_events_dlq
    }

    SyncWorkerSystem --> StreamProcessor
    SyncWorkerSystem --> RedisStreamsClient
    SyncWorkerSystem --> SyncService
    SyncWorkerSystem --> ExternalSystems
```

## 2. Sequence Diagram - Message Processing

```mermaid
sequenceDiagram
    participant Redis Stream
    participant SyncWorker
    participant StreamProcessor
    participant SyncService
    participant ChromaDB

    Note over Redis Stream, ChromaDB: Message Processing Flow

    Redis Stream->>SyncWorker: 1. XREADGROUP (notes:events)
    SyncWorker->>Redis Stream: 2. Receive message batch
    SyncWorker->>StreamProcessor: 3. process_stream()
    SyncWorker->>SyncWorker: 4. _process_message()
    SyncWorker->>SyncService: 5. handle(event)
    SyncService->>ChromaDB: 6. embed text & upsert
    ChromaDB-->>SyncService: 7. Success response
    SyncService-->>SyncWorker: 8. Processing complete
    SyncWorker->>Redis Stream: 9. XACK message
```

## 3. State Machine Diagram - Message Lifecycle

```mermaid
stateDiagram-v2
    [*] --> Pending: Message received
    Pending --> Processing: Start processing
    Processing --> Success: Processed successfully
    Processing --> Failed: Processing failed
    
    Failed --> Retrying: Schedule retry
    Retrying --> Processing: Retry attempt
    Failed --> DLQ: Max retries exceeded
    
    Success --> Done: Acknowledged
    DLQ --> Done: Sent to DLQ
    
    state Retrying {
        [*] --> WaitDelay
        WaitDelay --> ReadyForRetry
        ReadyForRetry --> [*]
    }

    Done --> [*]
```

## 4. Activity Diagram - Stream Processing Workflow

```mermaid
flowchart TD
    Start([Start Worker]) --> EnsureGroup[Ensure Consumer Group Exists]
    EnsureGroup --> DrainPending[Drain Pending Messages]
    DrainPending --> LoopStart{Start Processing Loop}
    
    LoopStart --> AutoClaim[Auto-claim Stuck Messages]
    AutoClaim --> ReadNew[XREADGROUP for New Messages]
    ReadNew --> ProcessBatch[Process Message Batch]
    
    subgraph ProcessEachMessage [For each message]
        Direction1[Check duplicate idempotency]
        Direction2[Process via SyncService]
        Direction3[Success: XACK]
        Direction4[Failure: Retry or DLQ]
    end
    
    ProcessBatch --> ProcessEachMessage
    ProcessEachMessage --> CheckShutdown{Shutdown?}
    
    CheckShutdown -- No --> LoopStart
    CheckShutdown -- Yes --> Cleanup[Execute Cleanup Handlers]
    Cleanup --> Stop([Stop Worker])
```

## 5. Component Interaction Diagram

```mermaid
flowchart LR
    subgraph A [Input Systems]
        API[API Service]
        DB[Database]
    end

    subgraph B [Stream Processing]
        Redis[Redis Stream]
        Worker[SyncWorker]
        SyncSvc[SyncService]
    end

    subgraph C [Output Systems]
        Chroma[ChromaDB]
        DLQ[Dead Letter Queue]
    end

    subgraph D [Control Systems]
        Retry[Retry Mechanism]
        Signals[Signal Handling]
    end

    API -->|emit_event| Redis
    DB -->|Note CRUD| Redis
    
    Redis -->|XREADGROUP| Worker
    Worker -->|handle| SyncSvc
    SyncSvc -->|embed & upsert| Chroma
    
    Worker -->|XACK| Redis
    Worker -->|Retry logic| Retry
    Retry -->|Exponential backoff| Worker
    
    Worker -->|XADD| DLQ
    Signals -->|Graceful shutdown| Worker
    
    style A fill:#e1f5fe
    style B fill:#f3e5f5
    style C fill:#e8f5e8
    style D fill:#fff3e0
```

## 6. Consumer Group Architecture

```mermaid
flowchart TB
    subgraph RedisStream[Redis Stream: notes:events]
        Msg1[Message 1]
        Msg2[Message 2]
        Msg3[Message 3]
        Msg4[Message 4]
    end

    subgraph ConsumerGroup[Consumer Group: sync-workers]
        Consumer1[Worker-1]
        Consumer2[Worker-2]
        Consumer3[Worker-3]
    end

    Msg1 --> Consumer1
    Msg2 --> Consumer2
    Msg3 --> Consumer3
    Msg4 --> Consumer1

    Consumer1 -->|XACK| RedisStream
    Consumer2 -->|XACK| RedisStream
    Consumer3 -->|XACK| RedisStream

    subgraph AutoClaim[Auto-Claim Process]
        AC[Check idle messages]
        AC -->|XCLAIM| Reassign[Reassign to active consumers]
    end

    Reassign --> Consumer1
    Reassign --> Consumer2
    Reassign --> Consumer3
```

These Mermaid diagrams visualize:

1. **Composite Structure**: The main components and their relationships
2. **Sequence Flow**: How messages are processed from Redis to ChromaDB
3. **State Machine**: The lifecycle of a message through the system
4. **Activity Workflow**: The overall processing loop with error handling
5. **Component Interaction**: How different parts of the system work together
6. **Consumer Groups**: How multiple workers load balance messages

You can use these diagrams in your documentation to explain the architecture and behavior of your Redis Streams worker system!