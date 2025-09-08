# NLIP Async Client

This is a very simple refinement of an HTTPX Async Client for sending and receiving NLIP Messages.  It illustrates how to serialize and deserialize NLIP Messages with a standard Python HTTP client.

By default, an `httpx.AsyncClient` instance keeps a Cookie store.  The Cookie store is necessary for interacting with the Agents in this project.  An Agent keeps a message history, which is associated with an HTTP Session.
