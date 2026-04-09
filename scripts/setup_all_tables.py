#!/usr/bin/env python3
"""
Setup all database tables in the correct order.
Creates SQLite tables for relational data and LanceDB tables for vector embeddings.
"""
import os
import sys

# Add parent directory to path so config imports work
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.database import get_connection, get_vector_db

EMBEDDING_DIMENSION = 384


def create_classified_emails_table(cursor):
    print("Creating classified_emails table...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS classified_emails (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            gmail_id TEXT UNIQUE NOT NULL,
            thread_id TEXT,
            subject TEXT,
            sender_email TEXT,
            sender_name TEXT,
            recipient_emails TEXT,
            cc_emails TEXT,
            bcc_emails TEXT,
            date_sent TEXT,
            date_received TEXT DEFAULT (datetime('now')),
            body_text TEXT,
            body_html TEXT,
            normalized_body_text TEXT,
            normalized_body_html TEXT,
            snippet TEXT,
            labels TEXT,
            has_attachments INTEGER DEFAULT 0,
            attachment_count INTEGER DEFAULT 0,
            importance_score REAL,
            processed INTEGER DEFAULT 0,
            raw_size INTEGER,

            -- Email headers for threading
            message_id TEXT,
            in_reply_to TEXT,
            "references" TEXT,

            -- Deduplication fields
            content_fingerprint TEXT,
            duplicate_group_id INTEGER,
            normalization_version INTEGER DEFAULT 2,

            -- Pipeline integration fields
            pipeline_processed INTEGER DEFAULT 0,
            embeddings_created INTEGER DEFAULT 0,
            enhanced_embedding_created INTEGER DEFAULT 0,
            chunks_created INTEGER DEFAULT 0,
            human_verified INTEGER DEFAULT 0,

            created_at TEXT DEFAULT (datetime('now')),
            updated_at TEXT DEFAULT (datetime('now'))
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_classified_emails_gmail_id ON classified_emails(gmail_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_classified_emails_thread ON classified_emails(thread_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_classified_emails_date ON classified_emails(date_sent)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_classified_emails_sender ON classified_emails(sender_email)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_classified_emails_processed ON classified_emails(pipeline_processed)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_classified_emails_fingerprint ON classified_emails(content_fingerprint)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_classified_emails_duplicate_group ON classified_emails(duplicate_group_id)")
    print("  classified_emails table created")


def create_email_fingerprints_table(cursor):
    print("Creating email_fingerprints_v2 table...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS email_fingerprints_v2 (
            email_id INTEGER PRIMARY KEY REFERENCES classified_emails(id) ON DELETE CASCADE,
            new_content_hash TEXT,
            quoted_content_hash TEXT,
            full_content_hash TEXT,
            structure_hash TEXT,
            thread_hash TEXT,
            recipient_set_hash TEXT,
            has_meaningful_new_content INTEGER DEFAULT 1,
            new_content_intent TEXT,
            email_type TEXT DEFAULT 'original',
            parsing_confidence REAL DEFAULT 1.0,
            is_canonical INTEGER DEFAULT 1,
            canonical_email_id INTEGER,
            fingerprint_version INTEGER DEFAULT 5,
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_fingerprints_v2_full_content ON email_fingerprints_v2(full_content_hash)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_fingerprints_v2_structure ON email_fingerprints_v2(structure_hash)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_fingerprints_v2_composite ON email_fingerprints_v2(full_content_hash, structure_hash)")
    print("  email_fingerprints_v2 table created")


def create_email_duplicate_groups_table(cursor):
    print("Creating email_duplicate_groups table...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS email_duplicate_groups (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content_fingerprint TEXT,
            primary_email_id INTEGER REFERENCES classified_emails(id),
            member_count INTEGER DEFAULT 1,
            first_seen TEXT,
            last_seen TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            updated_at TEXT DEFAULT (datetime('now')),
            normalization_version INTEGER DEFAULT 5
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_duplicate_groups_fingerprint ON email_duplicate_groups(content_fingerprint)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_duplicate_groups_primary ON email_duplicate_groups(primary_email_id)")
    print("  email_duplicate_groups table created")


def create_customer_issues_table(cursor):
    print("Creating customer_issues table...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS customer_issues (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email_id INTEGER REFERENCES classified_emails(id),
            customer_email TEXT NOT NULL,
            customer_name TEXT,
            issue_description TEXT,
            urgency_score REAL CHECK (urgency_score >= 0 AND urgency_score <= 1),
            sentiment_score REAL CHECK (sentiment_score >= -1 AND sentiment_score <= 1),
            category TEXT,
            subcategory TEXT,
            product_name TEXT,
            order_number TEXT,
            priority TEXT CHECK (priority IN ('low', 'medium', 'high', 'urgent')),
            status TEXT DEFAULT 'new',
            thread_id TEXT,
            related_emails TEXT,
            extracted_entities TEXT,
            ai_summary TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            updated_at TEXT DEFAULT (datetime('now'))
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_customer_issues_email ON customer_issues(customer_email)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_customer_issues_status ON customer_issues(status)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_customer_issues_priority ON customer_issues(priority)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_customer_issues_created ON customer_issues(created_at)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_customer_issues_thread ON customer_issues(thread_id)")
    print("  customer_issues table created")


def create_parsed_emails_table(cursor):
    print("Creating parsed_emails table...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS parsed_emails (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email_id INTEGER REFERENCES classified_emails(id) ON DELETE CASCADE,
            new_content TEXT,
            quoted_content TEXT,
            quote_headers TEXT,
            parsing_method TEXT,
            confidence_score REAL DEFAULT 1.0,
            metadata TEXT DEFAULT '{}',
            created_at TEXT DEFAULT (datetime('now')),
            UNIQUE(email_id)
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_parsed_emails_email_id ON parsed_emails(email_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_parsed_emails_method ON parsed_emails(parsing_method)")
    print("  parsed_emails table created")


def create_email_pipeline_routes_table(cursor):
    print("Creating email_pipeline_routes table...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS email_pipeline_routes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email_id INTEGER REFERENCES classified_emails(id),
            pipeline_type TEXT,
            priority_score REAL,
            status TEXT DEFAULT 'pending',
            assigned_to TEXT,
            processing_notes TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            updated_at TEXT DEFAULT (datetime('now')),
            UNIQUE(email_id, pipeline_type)
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_pipeline_routes_email ON email_pipeline_routes(email_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_pipeline_routes_type ON email_pipeline_routes(pipeline_type)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_pipeline_routes_status ON email_pipeline_routes(status)")
    print("  email_pipeline_routes table created")


def create_email_classifications_table(cursor):
    print("Creating email_classifications table...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS email_classifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email_id INTEGER REFERENCES classified_emails(id),
            classification_type TEXT,
            confidence_score REAL,
            created_at TEXT DEFAULT (datetime('now')),
            UNIQUE(email_id, classification_type)
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_email_classifications_email ON email_classifications(email_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_email_classifications_type ON email_classifications(classification_type)")
    print("  email_classifications table created")


def create_pipeline_outcomes_table(cursor):
    print("Creating pipeline_outcomes table...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pipeline_outcomes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email_id INTEGER REFERENCES classified_emails(id),
            pipeline_type TEXT,
            outcome_type TEXT,
            outcome_details TEXT,
            revenue_generated REAL,
            articles_published INTEGER DEFAULT 0,
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_pipeline_outcomes_email ON pipeline_outcomes(email_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_pipeline_outcomes_type ON pipeline_outcomes(outcome_type)")
    print("  pipeline_outcomes table created")


def create_classification_performance_table(cursor):
    print("Creating classification_performance table...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS classification_performance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            classification_type TEXT,
            true_positives INTEGER DEFAULT 0,
            false_positives INTEGER DEFAULT 0,
            false_negatives INTEGER DEFAULT 0,
            precision_score REAL,
            recall_score REAL,
            f1_score REAL,
            last_updated TEXT DEFAULT (datetime('now'))
        )
    """)
    print("  classification_performance table created")


def create_enhanced_email_embeddings_table(cursor):
    print("Creating enhanced_email_embeddings table...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS enhanced_email_embeddings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email_id INTEGER REFERENCES classified_emails(id) ON DELETE CASCADE,
            gmail_id TEXT,
            embedding_type TEXT NOT NULL,
            embedding_text TEXT,

            thread_id TEXT,
            sender_email TEXT,
            pipeline_classification TEXT,
            sender_interaction_count INTEGER,
            thread_message_count INTEGER,

            includes_response INTEGER DEFAULT 0,
            includes_thread_context INTEGER DEFAULT 0,
            includes_sender_history INTEGER DEFAULT 0,
            includes_pipeline_context INTEGER DEFAULT 0,
            related_article_count INTEGER DEFAULT 0,

            search_keywords TEXT,
            business_context TEXT,
            context_summary TEXT,

            created_at TEXT DEFAULT (datetime('now')),
            updated_at TEXT DEFAULT (datetime('now')),

            UNIQUE(email_id, embedding_type)
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_enhanced_embeddings_email ON enhanced_email_embeddings(email_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_enhanced_embeddings_type ON enhanced_email_embeddings(embedding_type)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_enhanced_embeddings_sender ON enhanced_email_embeddings(sender_email)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_enhanced_embeddings_pipeline ON enhanced_email_embeddings(pipeline_classification)")
    print("  enhanced_email_embeddings table created")


def create_sender_interaction_history_table(cursor):
    print("Creating sender_interaction_history table...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sender_interaction_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender_email TEXT,
            sender_name TEXT,

            total_emails_sent INTEGER DEFAULT 0,
            total_emails_responded INTEGER DEFAULT 0,
            total_emails_received INTEGER DEFAULT 0,
            first_contact_date TEXT,
            last_contact_date TEXT,

            relationship_type TEXT,
            interaction_quality TEXT,
            response_rate REAL,
            avg_response_time_hours REAL,

            total_revenue_generated REAL DEFAULT 0,
            articles_published INTEGER DEFAULT 0,
            meetings_held INTEGER DEFAULT 0,

            common_topics TEXT,
            pipeline_history TEXT,
            notes TEXT,

            created_at TEXT DEFAULT (datetime('now')),
            updated_at TEXT DEFAULT (datetime('now')),

            UNIQUE(sender_email)
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_sender_history_email ON sender_interaction_history(sender_email)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_sender_history_type ON sender_interaction_history(relationship_type)")
    print("  sender_interaction_history table created")


def create_thread_context_table(cursor):
    print("Creating thread_context table...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS thread_context (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            gmail_thread_id TEXT UNIQUE,

            participant_emails TEXT,
            participant_names TEXT,
            thread_message_count INTEGER DEFAULT 0,
            message_count INTEGER DEFAULT 0,
            our_message_count INTEGER DEFAULT 0,

            thread_type TEXT,
            thread_status TEXT,
            primary_pipeline TEXT,

            thread_start_date TEXT,
            started_date TEXT,
            last_activity_date TEXT,

            thread_summary TEXT,
            key_topics TEXT,
            business_outcome TEXT,

            created_at TEXT DEFAULT (datetime('now')),
            updated_at TEXT DEFAULT (datetime('now'))
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_thread_context_gmail_id ON thread_context(gmail_thread_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_thread_context_pipeline ON thread_context(primary_pipeline)")
    print("  thread_context table created")


def create_pipeline_context_enrichment_table(cursor):
    print("Creating pipeline_context_enrichment table...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pipeline_context_enrichment (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email_id INTEGER UNIQUE REFERENCES classified_emails(id),
            pipeline_type TEXT,

            related_articles TEXT,
            sender_business_profile TEXT,
            competitive_analysis TEXT,
            suggested_responses TEXT,
            response_templates TEXT,

            created_at TEXT DEFAULT (datetime('now'))
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_pipeline_enrichment_email ON pipeline_context_enrichment(email_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_pipeline_enrichment_pipeline ON pipeline_context_enrichment(pipeline_type)")
    print("  pipeline_context_enrichment table created")


def create_customer_issues_v2_table(cursor):
    print("Creating customer_issues_v2 table...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS customer_issues_v2 (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email_id INTEGER REFERENCES classified_emails(id),
            thread_id TEXT,
            issue_type TEXT,
            issue_category TEXT,
            issue_summary TEXT,
            has_resolution INTEGER DEFAULT 0,
            resolution_summary TEXT,
            fix_instructions TEXT,
            similarity_score REAL,
            based_on_issues TEXT,
            confidence_level TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            updated_at TEXT DEFAULT (datetime('now'))
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_customer_issues_v2_email ON customer_issues_v2(email_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_customer_issues_v2_thread ON customer_issues_v2(thread_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_customer_issues_v2_type ON customer_issues_v2(issue_type)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_customer_issues_v2_category ON customer_issues_v2(issue_category)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_customer_issues_v2_resolution ON customer_issues_v2(has_resolution)")
    print("  customer_issues_v2 table created")


def create_resolution_feedback_table(cursor):
    print("Creating resolution_feedback table...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS resolution_feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            issue_id INTEGER REFERENCES customer_issues_v2(id),
            was_effective INTEGER,
            feedback_text TEXT,
            feedback_date TEXT DEFAULT (datetime('now'))
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_resolution_feedback_issue ON resolution_feedback(issue_id)")
    print("  resolution_feedback table created")


def create_issue_similarity_cache_table(cursor):
    print("Creating issue_similarity_cache table...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS issue_similarity_cache (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_issue_id INTEGER REFERENCES customer_issues_v2(id),
            similar_issue_id INTEGER REFERENCES customer_issues_v2(id),
            similarity_score REAL,
            created_at TEXT DEFAULT (datetime('now')),
            UNIQUE(source_issue_id, similar_issue_id)
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_similarity_cache_source ON issue_similarity_cache(source_issue_id)")
    print("  issue_similarity_cache table created")


def setup_lancedb_tables(vector_db):
    """Create LanceDB tables for vector embeddings."""
    import pyarrow as pa

    print("\nSetting up LanceDB vector tables...")

    # email_chunk_vectors: stores chunked email embeddings
    if "email_chunk_vectors" not in vector_db.table_names():
        schema = pa.schema([
            pa.field("email_id", pa.int64()),
            pa.field("chunk_index", pa.int32()),
            pa.field("chunk_type", pa.string()),
            pa.field("text", pa.string()),
            pa.field("vector", pa.list_(pa.float32(), EMBEDDING_DIMENSION)),
            pa.field("metadata", pa.string()),
        ])
        vector_db.create_table("email_chunk_vectors", schema=schema)
        print("  email_chunk_vectors table created")
    else:
        print("  email_chunk_vectors table already exists")

    # enhanced_embedding_vectors: stores context-enriched embeddings
    if "enhanced_embedding_vectors" not in vector_db.table_names():
        schema = pa.schema([
            pa.field("email_id", pa.int64()),
            pa.field("embedding_type", pa.string()),
            pa.field("vector", pa.list_(pa.float32(), EMBEDDING_DIMENSION)),
        ])
        vector_db.create_table("enhanced_embedding_vectors", schema=schema)
        print("  enhanced_embedding_vectors table created")
    else:
        print("  enhanced_embedding_vectors table already exists")

    # issue_embedding_vectors: stores issue and resolution embeddings
    if "issue_embedding_vectors" not in vector_db.table_names():
        schema = pa.schema([
            pa.field("issue_id", pa.int64()),
            pa.field("embedding_type", pa.string()),
            pa.field("vector", pa.list_(pa.float32(), EMBEDDING_DIMENSION)),
        ])
        vector_db.create_table("issue_embedding_vectors", schema=schema)
        print("  issue_embedding_vectors table created")
    else:
        print("  issue_embedding_vectors table already exists")


def main():
    """Create all tables in correct dependency order."""
    try:
        conn = get_connection()
        cursor = conn.cursor()

        print("Setting up SQLite database...\n")

        # Core email tables
        create_classified_emails_table(cursor)
        create_email_fingerprints_table(cursor)
        create_email_duplicate_groups_table(cursor)
        create_customer_issues_table(cursor)
        create_parsed_emails_table(cursor)

        # Pipeline routing tables
        create_email_pipeline_routes_table(cursor)
        create_email_classifications_table(cursor)
        create_pipeline_outcomes_table(cursor)
        create_classification_performance_table(cursor)

        # Enhanced embedding metadata tables
        create_enhanced_email_embeddings_table(cursor)
        create_sender_interaction_history_table(cursor)
        create_thread_context_table(cursor)
        create_pipeline_context_enrichment_table(cursor)

        # Issue tracking v2
        create_customer_issues_v2_table(cursor)
        create_resolution_feedback_table(cursor)
        create_issue_similarity_cache_table(cursor)

        conn.commit()
        conn.close()

        # Set up LanceDB vector tables
        vector_db = get_vector_db()
        setup_lancedb_tables(vector_db)

        print("\nAll tables created successfully!")
        print("  SQLite tables: 16 (core + pipeline + embeddings + issue tracking)")
        print("  LanceDB tables: 3 (email chunks, enhanced embeddings, issue embeddings)")

    except Exception as e:
        print(f"\nError creating tables: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
