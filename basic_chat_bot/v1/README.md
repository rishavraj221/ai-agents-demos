## Part 1: A Basic Chatbot

A simple chatbot using LangGraph. It will respond directly to user messages. Though simple, it will illustrate the core concepts of building with LangGraph.

### Concept

While defining a graph, the first step is to define its `State`. The `State` includes the graph's schema and `reducer functions` that handle state updates.

`State` defined here is a `TypedDict` with one key: `messages`. The `add_messages` reducer function is used to append new messages to the list instead of overwriting it.

Keys without a reducer annotation will overwrite previous values.
