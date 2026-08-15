-- =====================================================
-- MBTI Divination Device — 扩展表（Task 1: AI玄学情绪解压搭子）
-- 依附于 01_schema.sql 的 users 表
-- =====================================================

-- ============ divination-service ============

CREATE TABLE IF NOT EXISTS divination_records (
    id              TEXT PRIMARY KEY,
    user_id         TEXT NOT NULL,
    type            TEXT NOT NULL CHECK (type IN ('tarot', 'astrology', 'dream', 'fortune')),
    question        TEXT,
    cards           JSONB,          -- [{"name":"The Fool","name_cn":"愚者","reversed":false,"position":"past","keyword":"新开始"}]
    interpretation  TEXT,
    emotion_before  TEXT,
    emotion_after   TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_div_user ON divination_records(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_div_type ON divination_records(user_id, type, created_at DESC);

-- ============ emotion-tracking-service ============

CREATE TABLE IF NOT EXISTS emotion_logs (
    id              TEXT PRIMARY KEY,
    user_id         TEXT NOT NULL,
    emotion         TEXT NOT NULL CHECK (emotion IN ('joy','calm','anxiety','sadness','anger','fear','surprise')),
    intensity       INT NOT NULL CHECK (intensity BETWEEN 1 AND 10),
    trigger_source  TEXT,
    context         TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_emotion_user_time ON emotion_logs(user_id, created_at DESC);

CREATE TABLE IF NOT EXISTS daily_emotion_summary (
    id              TEXT PRIMARY KEY,
    user_id         TEXT NOT NULL,
    date            DATE NOT NULL,
    avg_intensity   NUMERIC(4,2),
    dominant_emotion TEXT,
    emotion_range   JSONB,
    phq4_score      INT CHECK (phq4_score BETWEEN 0 AND 12),
    notes           TEXT,
    UNIQUE(user_id, date)
);

-- ============ task-service (gamification) ============

CREATE TABLE IF NOT EXISTS task_records (
    id              TEXT PRIMARY KEY,
    user_id         TEXT NOT NULL,
    task_type       TEXT NOT NULL CHECK (task_type IN ('check_in','mood_log','meditation','divination')),
    metadata        JSONB,
    points_earned   INT NOT NULL DEFAULT 0,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_task_user_time ON task_records(user_id, created_at DESC);

CREATE TABLE IF NOT EXISTS user_points (
    user_id         TEXT PRIMARY KEY,
    total_points    INT NOT NULL DEFAULT 0,
    level           INT NOT NULL DEFAULT 1,
    streak_days     INT NOT NULL DEFAULT 0,
    last_check_in   DATE,
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS achievements (
    id              TEXT PRIMARY KEY,
    user_id         TEXT NOT NULL,
    code            TEXT NOT NULL,
    unlocked_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(user_id, code)
);
CREATE INDEX IF NOT EXISTS idx_achievements_user ON achievements(user_id);
