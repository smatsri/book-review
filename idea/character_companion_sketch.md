# Character Companion Sketch

This note captures the product direction for a book-aware reading companion: not a generic chatbot, but a character that feels like it lives inside the reader's current story state.

## Core idea

The companion should know:

- which book the reader is reading
- which chapter or reading point they are at
- what has been revealed so far
- what remains locked as future story content
- how the chosen character speaks, thinks, and interprets events

The result is a spoiler-safe, in-character, reading-aware assistant instead of a generic AI summary bot.

## Why this is not just another prompt

A simple prompt-based bot is not enough because it does not understand the timeline of the book. If the user has read chapters 1–4, the companion should answer from that slice of the story only. It should not leak future plot or act like an omniscient narrator.

This means the system needs more than a single prompt. It needs:

- chapter-level story memory
- session state for the current reader position
- retrieval of only allowed content
- persona constraints for voice and worldview
- explicit spoiler protections

## Practical architecture

### 1. Book ingestion and chapter memory

- load the text or EPUB
- split into chapters
- extract characters, events, themes, quotes, and chapter summaries
- store per-chapter metadata

This is already aligned with the project’s chapter-analysis pipeline and rollup structure.

### 2. Reading state engine

For each user session, track:

- `book_id`
- `current_chapter`
- `current_reading_position`
- `known_events`
- `known_characters`
- `future_content_locked`
- `recent_questions` and prior answers

This is the state machine that keeps the companion grounded in the reader’s progress.

### 3. Character/persona layer

Define the companion as a persona with:

- voice and diction
- emotional tendencies
- worldview
- relation to other characters
- what it knows and what it may not know

This is the layer that makes the interaction feel like a real character rather than “AI with a book in context.”

### 4. Retrieval layer

The companion should retrieve only relevant prior context:

- recent chapters
- character arcs up to the current point
- theme and relationship data
- events from the current reading state

This is where embeddings or chapter-level vector search help a lot.

### 5. Spoiler guard

The system should actively enforce a timeline boundary:

- allowed: chapters already read
- blocked: future chapters, major reveals, and unresolved twists
- response policy: if the user asks about future content, say the companion does not know yet or the event has not reached them

This is critical for reader trust and immersion.

## Fine-tuning vs embeddings

There are two ways to “embed” the book into the system:

### A. Fine-tuning the model

This can help with:

- character voice
- tone consistency
- persona authenticity

But it is still static knowledge. It does not solve current chapter awareness or spoiler control by itself.

### B. RAG / embeddings / structured memory

This is often the better fit for a book companion because it makes the system:

- chapter-aware
- reading-state-aware
- spoiler-safe
- dynamically grounded in the actual content

## Best practical design

The strongest implementation is hybrid:

- LoRA or persona-tuning for voice consistency
- embeddings or vector retrieval for chapter knowledge
- explicit state tracking for the reader’s current progress
- hard boundaries on future content

This yields a system that feels like a character and behaves like a reading companion, not just a prompt wrapper around a book.

## MVP shape

A strong first version could be:

- one book
- one companion character
- spoiler-safe chapter tracking
- read-state-aware chat
- grounded on chapter summaries and character memory

Example actions:

- “Explain this scene to me as if you were the protagonist.”
- “What has happened so far from your perspective?”
- “Why did they make that decision?”
- “What should I watch for in the next chapter?”
- “Summarize the current state of the story without spoilers.”

## Product wedge

This is different from:

- generic AI chat
- generic book summaries
- annotation tools
- character roleplay without narrative memory

It is a persistent, story-aware companion that lives inside the current reading state and respects the narrative timeline.

That is the real product opportunity.
