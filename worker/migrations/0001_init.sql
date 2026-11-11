PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS books (
  id TEXT PRIMARY KEY,
  title TEXT NOT NULL,
  author TEXT,
  language TEXT NOT NULL DEFAULT 'bn',
  source_url TEXT,
  rights_type TEXT NOT NULL CHECK (rights_type IN ('public_domain', 'open_license', 'permission_granted')),
  rights_note TEXT NOT NULL,
  storage_key TEXT,
  status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'processing', 'ready', 'failed', 'archived')),
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS book_pages (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  book_id TEXT NOT NULL REFERENCES books(id) ON DELETE CASCADE,
  page_number INTEGER NOT NULL,
  chapter TEXT,
  content TEXT NOT NULL,
  content_hash TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(book_id, page_number)
);

CREATE VIRTUAL TABLE IF NOT EXISTS book_pages_fts USING fts5(
  book_id UNINDEXED,
  page_number UNINDEXED,
  chapter,
  content,
  tokenize = 'unicode61'
);

CREATE TRIGGER IF NOT EXISTS book_pages_fts_insert AFTER INSERT ON book_pages BEGIN
  INSERT INTO book_pages_fts(rowid, book_id, page_number, chapter, content)
  VALUES (new.id, new.book_id, new.page_number, COALESCE(new.chapter, ''), new.content);
END;

CREATE TRIGGER IF NOT EXISTS book_pages_fts_delete AFTER DELETE ON book_pages BEGIN
  DELETE FROM book_pages_fts WHERE rowid = old.id;
END;

CREATE TRIGGER IF NOT EXISTS book_pages_fts_update AFTER UPDATE ON book_pages BEGIN
  DELETE FROM book_pages_fts WHERE rowid = old.id;
  INSERT INTO book_pages_fts(rowid, book_id, page_number, chapter, content)
  VALUES (new.id, new.book_id, new.page_number, COALESCE(new.chapter, ''), new.content);
END;

CREATE TABLE IF NOT EXISTS admin_audit_log (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  admin_telegram_id TEXT NOT NULL,
  action TEXT NOT NULL,
  target_id TEXT,
  details TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_books_status ON books(status);
CREATE INDEX IF NOT EXISTS idx_book_pages_book_page ON book_pages(book_id, page_number);
