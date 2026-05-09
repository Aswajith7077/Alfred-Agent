# Obsidian Lazy Loading with Chroma Vector DB

## Overview

This implementation provides efficient lazy loading of Obsidian vault documents with integration to Chroma vector database. Only **required documents are loaded and synced** — the rest are never loaded into memory.

## How Lazy Loading Works

```python
# Documents are loaded ONE AT A TIME from the vault
# Memory only holds the current document being processed
# Unselected documents are NEVER loaded at all
```

### Traditional Approach (Memory Inefficient)
```
Load ALL documents → Filter them → Store to DB
❌ All documents loaded into memory first
```

### Lazy Loading Approach (Memory Efficient)
```
For each document:
  → Check filter → Store if match → Move to next
✅ Only matching documents loaded and stored
```

## Key Features

1. **Lazy Loading**: Documents loaded on-demand, one at a time
2. **Filtering**: Select specific documents before syncing
3. **Chroma DB Integration**: Vector embeddings stored persistently
4. **Batch Processing**: Efficient DB operations
5. **Search Capability**: Query synced documents by relevance

## Installation

Ensure these are in `requirements.txt`:
```
langchain-community
chromadb
langchain
```

## Basic Usage

### 1. Initialize the Service

```python
from apps.obsidian.service import Obsidian

obsidian = Obsidian(
    vault_path="C:\\Users\\YourUser\\ObsidianVault",
    db_path="vector-db/obsidian.db",
    embedding_model="nomic-embed-text"  # Ollama model
)
```

### 2. Sync All Documents

```python
obsidian.sync_to_vector_db()
```

### 3. Sync Only Selected Documents

```python
# Define a filter function
def filter_fn(doc):
    return "python" in doc.content.lower()

# Sync only matching documents
obsidian.sync_to_vector_db(filter_fn=filter_fn)
```

### 4. Search the Vector DB

```python
results = obsidian.query_vector_db("How to use Python?", k=5)

for content, metadata, score in results:
    print(f"Relevance: {score:.4f}")
    print(f"Source: {metadata.get('path')}")
    print(f"Content: {content[:200]}...")
```

## Filtering Examples

### Filter by File Size
```python
def large_docs(doc):
    return doc.filesize > 5000

obsidian.sync_to_vector_db(filter_fn=large_docs)
```

### Filter by Path Pattern
```python
def project_docs(doc):
    path = doc.metadata.get("path", "").lower()
    return any(p in path for p in ["project", "research", "learning"])

obsidian.sync_to_vector_db(filter_fn=project_docs)
```

### Filter by Content Keywords
```python
def important_docs(doc):
    keywords = ["important", "critical", "todo", "bug"]
    return any(kw in doc.content.lower() for kw in keywords)

obsidian.sync_to_vector_db(filter_fn=important_docs)
```

### Multiple Criteria Filter
```python
def selective_filter(doc):
    has_keyword = any(kw in doc.content.lower() 
                     for kw in ["python", "machine learning"])
    
    is_large = doc.filesize > 1000
    
    from_project = "projects" in doc.metadata.get("path", "").lower()
    
    return has_keyword and (is_large or from_project)

obsidian.sync_to_vector_db(filter_fn=selective_filter)
```

## Lazy Iterate Without Syncing

Preview documents without storing to vector DB:

```python
for doc in obsidian.lazy_load_documents():
    print(f"File: {doc.filename}")
    print(f"Size: {doc.filesize} bytes")
    print(f"Path: {doc.metadata.get('path')}")
    # Process document...
```

## API Reference

### `sync_to_vector_db(filter_fn=None, batch_size=10)`

Load documents lazily and sync to Chroma DB.

**Parameters:**
- `filter_fn` (callable, optional): Function returning True to include document
- `batch_size` (int): Number of document chunks to batch before DB insert

**Example:**
```python
obsidian.sync_to_vector_db(
    filter_fn=lambda doc: doc.filesize > 1000,
    batch_size=5
)
```

### `lazy_load_documents(filter_fn=None)`

Generator yielding documents one at a time.

**Parameters:**
- `filter_fn` (callable, optional): Filter function

**Returns:**
- Generator of Document objects

**Example:**
```python
for doc in obsidian.lazy_load_documents():
    # Process document
    pass
```

### `query_vector_db(query, k=5)`

Search the vector database.

**Parameters:**
- `query` (str): Search query
- `k` (int): Number of results to return

**Returns:**
- List of tuples: (content, metadata, relevance_score)

## Performance Notes

- **Memory**: Only current document in memory during sync
- **Speed**: Batched DB operations (default batch_size=10)
- **Storage**: Chroma DB persisted to `vector-db/obsidian.db`
- **Embeddings**: Using Ollama (ensure Ollama running)

## Troubleshooting

### Embeddings Connection Error
Ensure Ollama is running:
```bash
ollama serve
```

### Filter Function Not Working
Test your filter:
```python
for doc in obsidian.lazy_load_documents():
    if your_filter(doc):
        print(f"Matched: {doc.filename}")
```

### Vector DB Not Persisting
The service automatically calls `persist()` after syncing. To manually persist:
```python
obsidian.vector_db.persist()
```
