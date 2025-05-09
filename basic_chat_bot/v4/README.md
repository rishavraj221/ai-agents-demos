## Part 4: Human-in-the-loop

Agents can be unreliable and may need human input to successfully accomplish tasks. Similarly, for some actions, you may want to require human approval before running to ensure that everything is running as intended.

LangGraph's persistence layer supports human-in-the-loop workflows, allowing execution to pause and resume based on user feedback. The primary interface to this functionality is the interrupt function. Calling `interrupt` inside a node will pause execution. Execution can be resumed, together with new input from a human, by passing in a Command. `interrupt` is ergonomically similar to Python's built-in `input()`, with some caveats.
