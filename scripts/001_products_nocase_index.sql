BEGIN;

CREATE INDEX IF NOT EXISTS idx_products_name_nocase
  ON products(name COLLATE NOCASE);

COMMIT;
