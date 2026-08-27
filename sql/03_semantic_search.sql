-- Semantic-search template.
-- QUERY_VECTOR must be generated using the same
-- all-MiniLM-L6-v2 embedding model used for ticket vectors.

SELECT TOP 5
    TICKET_ID,
    TITLE,
    DESCRIPTION,
    PRODUCT_AREA,
    CATEGORY,
    ISSUE_FAMILY,
    COSINE_SIMILARITY(
        EMBEDDING,
        TO_REAL_VECTOR(:QUERY_VECTOR)
    ) AS SIMILARITY_SCORE
FROM SUPPORT_TICKETS
WHERE EMBEDDING IS NOT NULL
ORDER BY SIMILARITY_SCORE DESC;