# Singapore Knowledge Categories

| Category                 | What information should we retrieve?                                                   |
|--------------------------|----------------------------------------------------------------------------------------|
| Attractions              | Key sights, what makes them notable, and visitor considerations.                       |
| Neighbourhoods           | Character, highlights, and experiences available in each area.                         |
| Transportation           | How tourists move around Singapore, available transport modes, and practical guidance. |
| Culture & Practical Tips | Singapore's general climate, packing guidance, practical travel advice                             |
| Food & Local Experiences | Local dishes, hawker culture, and distinctive experiences to try.                      |
| Itineraries              | Example activity groupings for different trip lengths and interests.                   |
| Indoor Activities        | Museums, galleries, shopping, and other weather-independent options.                   |
| Outdoor Activities       | Parks, waterfronts, nature areas, and open-air experiences.                            |

## Design Questions

### 1. Why should source and URL be stored as metadata instead of being embedded inside the text itself?

Keeping the source and URL as metadata preserves the retrieved text for its actual travel content while retaining traceability. The application can show citations, filter by source, or update a document without those technical details affecting chunk relevance or the quality of generated answers.

### 2. Why might a `topic` metadata field be useful when testing our retriever?

A `topic` field lets us check whether a query retrieves chunks from the expected category, such as Transportation or Food & Local Experiences. This makes retrieval tests easier to evaluate and helps identify categories that need better source coverage or chunking.