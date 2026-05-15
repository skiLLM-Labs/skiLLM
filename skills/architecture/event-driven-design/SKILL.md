---
name: event-driven-design
description: When designing loosely coupled systems that react to state changes asynchronously.
version: 1.0.0
tags: [architecture, events, async]
---

# Event-Driven Design

## When to use
- De-coupling monolithic microservices.
- Implementing long-running asynchronous workflows (e.g., video processing).
- Triggering multiple side-effects across different domains from a single action.

## What it does
Uses events (facts about something that has already happened) as the primary communication mechanism between system components, increasing scalability and resilience.

## Workflow
1. **Define Events**: Identify state changes in the domain and model them as past-tense events (e.g., `OrderPlaced`, `UserRegistered`).
2. **Design Event Payloads**: Include the Event ID, Timestamp, Event Type, and the minimal required data payload.
3. **Publishing Mechanism**: Have the producer system emit the event to a Message Broker or Event Bus (e.g., Kafka, RabbitMQ, EventBridge) without caring who consumes it.
4. **Idempotent Consumers**: Ensure consumer services can process the same event multiple times without adverse side effects.
5. **Handle Failures**: Implement Dead Letter Queues (DLQ) for events that consumers repeatedly fail to process.

## Rules
- Events must be immutable; they cannot be changed or deleted once emitted.
- Consumers must be idempotent.
- Payloads should avoid containing deeply nested, rapidly changing entity graphs.

## Anti-patterns
- **Commands as Events**: Naming events like actions (`SendEmailEvent`) rather than facts (`UserCreated`).
- **Distributed Monolith**: Systems requiring synchronous HTTP calls *in response* to an event before completing their workflow.

## Output format
Schema definitions for event payloads, publisher emission logic, and idempotent consumer handler functions.
