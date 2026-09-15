# Singapore Knowledge Base Ingestion Plan

## 1. Raw Sources

| Source                               | Local File                      | Format | Main Coverage                                                                                                  |
|--------------------------------------|---------------------------------|--------|----------------------------------------------------------------------------------------------------------------|
| Wikivoyage Singapore Travel Guide    | wikivoyage_singapore.html       | HTML   | Neighbourhoods, attractions, activities, food, transport, culture, and practical tips.                         |
| Visit Singapore – Plan Your Trip     | visit_singapore_plan.html       | HTML   | Official visitor preparation, transport, payment basics, practical tips, events, and itinerary ideas.          |
| Visit Singapore – Travel Itineraries | visit_singapore_itineraries.pdf | PDF    | Multi-day itineraries, cultural and food experiences, attractions, and indoor, outdoor, and family activities. |

## 2. Document Metadata

Each document/chunk should preserve:

- source
- url
- topic
- page (when applicable)

## 3. Processing Pipeline

Source
→ Load
→ Clean
→ Create LangChain Documents
→ Split into chunks
→ Add/preserve metadata
→ Generate embeddings
→ Store in vector store

## 4. Why We Are Not Ingesting Everything

A focused knowledge base contains material that directly supports the assistant's intended travel-planning questions. This improves retrieval relevance, reduces duplicate or off-topic chunks, and makes answers easier to trace to reliable sources. It also avoids ingesting content outside the assignment scope, such as booking, reservations, navigation, and payment processing.

## 5. Reproducibility

Separate raw files provide a stable record of the exact source material used to create the knowledge base. We can rerun or improve cleaning, chunking, metadata, and embedding steps without downloading the sources again, making results easier to reproduce and compare. The processing code remains reusable while the raw files preserve source provenance.

## 6. Metadata Question

#### Why should metadata survive the chunking process instead of existing only on the original document?

Retrieval happens at the chunk level, so every chunk needs its own source, URL, topic, and page context. Preserving metadata lets the assistant cite the information it used, filter or evaluate results by category, and trace a retrieved passage back to its original document.