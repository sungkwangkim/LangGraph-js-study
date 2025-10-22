# Project Overview

This project implements a conversational agent using LangGraph.js. The agent is designed to answer questions about restaurants in Jamsil, Seoul, by retrieving information from a set of predefined blog posts. It uses a Retrieval-Augmented Generation (RAG) approach to provide answers.

The agent's workflow is structured as a graph, with nodes for different tasks such as retrieving documents, grading their relevance, rewriting the user's query, and generating a final answer.

## Technologies Used

*   **LangGraph.js:** A library for building stateful, multi-actor applications with LLMs.
*   **LangChain.js:** A framework for developing applications powered by language models.
*   **TypeScript:** The programming language used for the project.
*   **Node.js:** The runtime environment for the application.
*   **OpenAI API:** Used for generating text and creating vector embeddings.
*   **Cheerio:** Used for web scraping to load the content of blog posts.
*   **MemoryVectorStore:** An in-memory vector database for storing and retrieving documents.

## Architecture

The project follows a modular architecture, with different components responsible for specific tasks:

*   **`src/index.ts`:** The entry point of the application. It initializes the graph and starts the conversation.
*   **`src/agent/graph.ts`:** Defines the structure of the LangGraph agent, including the nodes and edges.
*   **`src/agent/edge.ts`:** Implements the logic for the nodes and conditional edges in the graph.
*   **`src/agent/tool.ts`:** Defines the tools available to the agent, such as the document retriever.
*   **`src/agent/retriever.ts`:** Configures the document retriever, including loading, splitting, and storing the documents.
*   **`src/agent/state.ts`:** Defines the state of the graph.

# Building and Running

To build and run the project, you need to have Node.js and npm installed.

1.  **Install dependencies:**

    ```bash
    npm install
    ```

2.  **Run the application:**

    ```bash
    npm run dev
    ```

# Development Conventions

*   **Coding Style:** The project uses TypeScript and follows standard coding conventions.
*   **Testing:** There are no explicit tests in the project.
*   **Contribution Guidelines:** There are no explicit contribution guidelines in the project.
