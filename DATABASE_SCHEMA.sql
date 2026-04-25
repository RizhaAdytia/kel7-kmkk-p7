-- ============================================================
-- SQL Schema untuk Database SPK dengan SAW & PROMETHEE II
-- ============================================================
-- Database: ahp.db (SQLite)
-- Dibuat otomatis oleh SQLAlchemy saat aplikasi run
-- ============================================================

-- ============================================================
-- Tabel Existing (AHP, MPE, Bayes, CPI)
-- ============================================================

CREATE TABLE IF NOT EXISTS project (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL
);

CREATE TABLE IF NOT EXISTS criterion (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL,
    project_id INTEGER NOT NULL,
    FOREIGN KEY (project_id) REFERENCES project(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS alternative (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL,
    project_id INTEGER NOT NULL,
    FOREIGN KEY (project_id) REFERENCES project(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS comparison (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    criterion_id INTEGER NOT NULL,
    item1_id INTEGER NOT NULL,
    item2_id INTEGER NOT NULL,
    value REAL NOT NULL,
    type VARCHAR(10) NOT NULL,  -- 'criteria' atau 'alternatives'
    FOREIGN KEY (criterion_id) REFERENCES criterion(id) ON DELETE CASCADE
);

-- ============================================================
-- Tabel Baru untuk SAW & PROMETHEE II
-- ============================================================

CREATE TABLE IF NOT EXISTS criterion_type (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    criterion_id INTEGER NOT NULL UNIQUE,
    is_benefit BOOLEAN DEFAULT 1,           -- 1 = Benefit, 0 = Cost
    weight_saw REAL DEFAULT 1.0,            -- Bobot untuk SAW
    weight_promethee REAL DEFAULT 1.0,      -- Bobot untuk PROMETHEE
    FOREIGN KEY (criterion_id) REFERENCES criterion(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS promethee_parameter (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    criterion_id INTEGER NOT NULL UNIQUE,
    p_threshold REAL DEFAULT 0.5,           -- Preference threshold
    q_threshold REAL DEFAULT 0.1,           -- Indifference threshold (q <= p)
    FOREIGN KEY (criterion_id) REFERENCES criterion(id) ON DELETE CASCADE
);

-- ============================================================
-- Index untuk Optimasi Query
-- ============================================================

CREATE INDEX IF NOT EXISTS idx_criterion_project 
ON criterion(project_id);

CREATE INDEX IF NOT EXISTS idx_alternative_project 
ON alternative(project_id);

CREATE INDEX IF NOT EXISTS idx_comparison_criterion 
ON comparison(criterion_id);

CREATE INDEX IF NOT EXISTS idx_criterion_type_criterion 
ON criterion_type(criterion_id);

CREATE INDEX IF NOT EXISTS idx_promethee_param_criterion 
ON promethee_parameter(criterion_id);

-- ============================================================
-- Sample Query untuk Testing
-- ============================================================

-- Lihat semua project
-- SELECT * FROM project;

-- Lihat kriteria beserta tipe dan bobot
-- SELECT c.id, c.name, ct.is_benefit, ct.weight_saw, ct.weight_promethee
-- FROM criterion c
-- LEFT JOIN criterion_type ct ON c.id = ct.criterion_id;

-- Lihat parameter PROMETHEE
-- SELECT c.id, c.name, pp.p_threshold, pp.q_threshold
-- FROM criterion c
-- LEFT JOIN promethee_parameter pp ON c.id = pp.criterion_id;

-- Count kriteria per project
-- SELECT p.id, p.name, COUNT(c.id) as jumlah_kriteria
-- FROM project p
-- LEFT JOIN criterion c ON p.id = c.project_id
-- GROUP BY p.id;

-- ============================================================
-- Notes:
-- - SQLite otomatis membuat table saat aplikasi Flask run
-- - Constraint UNIQUE pada criterion_id memastikan hanya 1 record per kriteria
-- - ON DELETE CASCADE memastikan data child terhapus saat parent dihapus
-- - Boolean di SQLite disimpan sebagai INTEGER (1=True, 0=False)
-- ============================================================
