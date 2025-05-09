### v2 Limitations

- Chatbot can't remember past interactions on its own, limiting its ability to have coherent, multi-turn conversations. In this version, we have added memory to address this.

## Part 3: Adding memory to the chatbot

- LangGraph solves this problem through **persistent checkpointing**. If you provide a `checkpointer` when compiling the graph and a `thread_id` when calling the graph, LangGraph automatically saves the state after each step. When you invoke the graph again using the same `thread_id`, the graph loads its saved state, allowing the chatbot to pickup where it left off.

- **checkpointing** is much more powerful than simple chat memory, it lets you save and resume complex state at any time for error recovery, human-in-the-loop workflows, time travel interactions, and more.
