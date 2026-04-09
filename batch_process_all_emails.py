#!/usr/bin/env python3
"""
Process ALL remaining emails - both short and regular
Creates chunks and embeddings stored in LanceDB for vector search.
"""

import os
import json
from sentence_transformers import SentenceTransformer
import sys
import time
import re
import traceback
from datetime import datetime
from config.database import get_connection, get_vector_db

BATCH_SIZE = 200
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"


class CompleteProcessor:
    def __init__(self):
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Initializing complete processor...")

        # Check if we're in offline mode
        if os.environ.get('HF_HUB_OFFLINE') == '1':
            snapshot_path = os.path.expanduser("~/.cache/huggingface/hub/models--sentence-transformers--all-MiniLM-L6-v2/snapshots/c9745ed1d9f207416be6d2e6f8de32d1f16199bf")
            if os.path.exists(snapshot_path):
                self.model = SentenceTransformer(snapshot_path, device='cpu')
            else:
                self.model = SentenceTransformer(EMBEDDING_MODEL, device='cpu', local_files_only=True)
        else:
            self.model = SentenceTransformer(EMBEDDING_MODEL, device='cpu')

        self.conn = get_connection()
        self.vector_db = get_vector_db()
        self.chunk_table = self.vector_db.open_table("email_chunk_vectors")
        print(f"Database connected successfully")

    def process_short_emails(self):
        """Process emails with body text < 50 chars"""
        cur = self.conn.cursor()
        cur.execute("""
            SELECT id, subject, snippet, sender_email, body_text
            FROM classified_emails
            WHERE chunks_created = 0
            AND LENGTH(COALESCE(body_text, '')) < 50
            AND (subject IS NOT NULL OR snippet IS NOT NULL)
            ORDER BY id DESC
            LIMIT ?
        """, (BATCH_SIZE * 2,))

        emails = cur.fetchall()
        if not emails:
            return 0

        texts = []
        for email in emails:
            text = f"Subject: {email['subject'] or 'No Subject'}\n"
            if email['snippet']:
                text += f"Preview: {email['snippet'][:500]}"
            elif email['body_text'] and len(email['body_text'].strip()) > 0:
                text += f"Body: {email['body_text'].strip()}"
            texts.append(text)

        embeddings = self.model.encode(texts, batch_size=32, show_progress_bar=False)

        # Insert vectors into LanceDB
        lance_rows = []
        email_ids = []
        for email, embedding, text in zip(emails, embeddings, texts):
            metadata = json.dumps({
                'email_id': email['id'],
                'type': 'short_email',
                'subject': email['subject'] or ''
            })
            lance_rows.append({
                "email_id": int(email['id']),
                "chunk_index": 0,
                "chunk_type": "body",
                "text": text[:500],
                "vector": embedding.tolist(),
                "metadata": metadata
            })
            email_ids.append(email['id'])

        if lance_rows:
            self.chunk_table.add(lance_rows)

        # Mark emails as chunked in SQLite
        cur.executemany(
            "UPDATE classified_emails SET chunks_created = 1, embeddings_created = 1 WHERE id = ?",
            [(eid,) for eid in email_ids]
        )
        self.conn.commit()
        return len(emails)

    def process_regular_emails(self):
        """Process all remaining emails"""
        cur = self.conn.cursor()
        cur.execute("""
            SELECT id, subject, body_text, body_html, snippet
            FROM classified_emails
            WHERE chunks_created = 0
            ORDER BY LENGTH(COALESCE(body_text, '')) ASC
            LIMIT ?
        """, (BATCH_SIZE,))

        emails = cur.fetchall()
        if not emails:
            return 0

        processed_count = 0
        lance_rows = []
        processed_ids = []

        for email in emails:
            try:
                text = email['body_text'] or ''
                if not text and email['body_html']:
                    text = re.sub('<[^<]+?>', '', email['body_html'])

                # For very short emails, include subject and snippet
                if len(text.strip()) < 50:
                    combined_text = f"Subject: {email['subject'] or 'No Subject'}\n"
                    if text.strip():
                        combined_text += f"Body: {text.strip()}\n"
                    if email['snippet']:
                        combined_text += f"Preview: {(email['snippet'] or '')[:200]}"

                    embedding = self.model.encode([combined_text], show_progress_bar=False)[0]
                    lance_rows.append({
                        "email_id": int(email['id']),
                        "chunk_index": 0,
                        "chunk_type": "body",
                        "text": combined_text[:500],
                        "vector": embedding.tolist(),
                        "metadata": json.dumps({'type': 'short_email'})
                    })
                    processed_ids.append(email['id'])
                    processed_count += 1
                    continue

                # Truncate very long emails
                if len(text) > 50000:
                    text = text[:50000] + "... [TRUNCATED]"

                # Clean text
                text = re.sub(r'https?://[^\s]+', ' [URL] ', text)
                text = re.sub(r'\s+', ' ', text)

                # Simple word-based chunking for longer emails
                words = text.split()
                chunks = []
                current = []
                size = 0

                for word in words:
                    if size + len(word) + 1 > 500 and current:
                        chunk_text = ' '.join(current)
                        if len(chunk_text) > 50:
                            chunks.append(chunk_text)
                        current = [word]
                        size = len(word)
                    else:
                        current.append(word)
                        size += len(word) + 1

                if current:
                    chunk_text = ' '.join(current)
                    if len(chunk_text) > 50:
                        chunks.append(chunk_text)

                # Limit chunks per email
                chunks = chunks[:30]

                if chunks:
                    embeddings = self.model.encode(chunks, batch_size=32, show_progress_bar=False)

                    for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                        metadata = json.dumps({
                            'email_id': int(email['id']),
                            'chunk_index': i,
                            'total_chunks': len(chunks)
                        })
                        lance_rows.append({
                            "email_id": int(email['id']),
                            "chunk_index": i,
                            "chunk_type": "body",
                            "text": chunk[:500],
                            "vector": embedding.tolist(),
                            "metadata": metadata
                        })

                    processed_ids.append(email['id'])
                    processed_count += 1
                else:
                    # No valid chunks — insert placeholder
                    lance_rows.append({
                        "email_id": int(email['id']),
                        "chunk_index": 0,
                        "chunk_type": "body",
                        "text": "SKIPPED: No valid chunks after processing",
                        "vector": [0.0] * 384,
                        "metadata": json.dumps({'reason': 'no_valid_chunks'})
                    })
                    processed_ids.append(email['id'])

            except Exception as e:
                # Mark as processed with error
                try:
                    lance_rows.append({
                        "email_id": int(email['id']),
                        "chunk_index": 0,
                        "chunk_type": "body",
                        "text": f"ERROR: {str(e)[:100]}",
                        "vector": [0.0] * 384,
                        "metadata": json.dumps({'error': str(e)[:200]})
                    })
                    processed_ids.append(email['id'])
                except Exception as inner_e:
                    print(f"WARNING: Failed to mark email {email['id']} as error: {inner_e}")
                    print(f"  Original error was: {str(e)[:200]}")
                    traceback.print_exc()

        # Batch write to LanceDB
        if lance_rows:
            self.chunk_table.add(lance_rows)

        # Mark emails as chunked in SQLite
        if processed_ids:
            cur.executemany(
                "UPDATE classified_emails SET chunks_created = 1, embeddings_created = 1 WHERE id = ?",
                [(eid,) for eid in processed_ids]
            )
        self.conn.commit()
        return processed_count

    def run(self):
        """Process all emails"""
        start_time = time.time()
        total_short = 0
        total_regular = 0
        batch = 0

        while True:
            batch += 1

            # Process short emails
            short_count = self.process_short_emails()
            total_short += short_count

            # Process regular emails
            regular_count = self.process_regular_emails()
            total_regular += regular_count

            if short_count == 0 and regular_count == 0:
                break

            # Stats
            elapsed = time.time() - start_time
            rate = (total_short + total_regular) / (elapsed / 60)

            print(f"[Batch {batch}] Short: {short_count}, Regular: {regular_count} | Total: {total_short + total_regular} | Rate: {rate:.0f}/min")

            # Check progress
            cur = self.conn.cursor()
            cur.execute("SELECT COUNT(*) FROM classified_emails WHERE chunks_created = 1")
            chunked = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM classified_emails")
            total = cur.fetchone()[0]
            if total > 0:
                print(f"  Progress: {chunked:,}/{total:,} ({chunked/total*100:.1f}%)")
            else:
                print(f"  Progress: no emails in database")

        print(f"\nCompleted in {(time.time() - start_time)/60:.1f} minutes")
        print(f"Processed: {total_short} short + {total_regular} regular = {total_short + total_regular} total")

    def close(self):
        self.conn.close()


if __name__ == "__main__":
    processor = CompleteProcessor()
    try:
        processor.run()
    except KeyboardInterrupt:
        print("\nStopped by user")
    finally:
        processor.close()
