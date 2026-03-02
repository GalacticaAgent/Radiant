-- Enable pgvector and migrate embeddings table if it previously used JSONB vector column

CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS external_papers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source VARCHAR(50) NOT NULL,
    external_id VARCHAR(200) NOT NULL,
    title TEXT NOT NULL,
    abstract TEXT,
    year INTEGER,
    venue TEXT,
    url TEXT,
    external_ids JSONB,
    fields_of_study JSONB,
    citation_count INTEGER,
    raw JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_external_papers_source_external_id UNIQUE (source, external_id)
);

CREATE INDEX IF NOT EXISTS idx_external_papers_title ON external_papers(title);
CREATE INDEX IF NOT EXISTS idx_external_papers_source ON external_papers(source);

DO $$
BEGIN
  IF EXISTS (
    SELECT 1
    FROM information_schema.columns
    WHERE table_name = 'embeddings' AND column_name = 'vector'
  ) THEN
    IF EXISTS (
      SELECT 1
      FROM information_schema.columns
      WHERE table_name = 'embeddings' AND column_name = 'vector'
        AND udt_name = 'jsonb'
    ) THEN
      IF NOT EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_name = 'embeddings' AND column_name = 'vector_jsonb'
      ) THEN
        ALTER TABLE embeddings RENAME COLUMN vector TO vector_jsonb;
      ELSE
        ALTER TABLE embeddings DROP COLUMN vector;
      END IF;
    END IF;
  END IF;

  IF NOT EXISTS (
    SELECT 1
    FROM information_schema.columns
    WHERE table_name = 'embeddings' AND column_name = 'vector'
  ) THEN
    ALTER TABLE embeddings ADD COLUMN vector vector(768);
  END IF;
END $$;

CREATE INDEX IF NOT EXISTS idx_embeddings_vector_hnsw ON embeddings USING hnsw (vector vector_cosine_ops);
