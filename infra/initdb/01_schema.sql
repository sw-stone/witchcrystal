-- MBTI Pet Island 数据库 schema —— 对应 TASKTODO Task 1.1：
-- "数据库设计：用户表、好友关系表、电子宠物状态表、Agent 交互日志表 (Daily Logs)"
--
-- 由 docker-entrypoint-initdb.d 在容器首次初始化时执行。
-- 已有数据卷时不会重跑；重建：docker compose -f infra/docker-compose.yml down -v && up -d
--
-- 设计约定：
-- - id 均为服务侧生成的 uuid 文本（与现有内存实现一致，避免 DB 生成 id 造成模型分叉）
-- - 时间戳统一 timestamptz；对外 API 仍输出 ISO 字符串（repository 层转换）
-- - JSON 契约为 camelCase，但列名 snake_case（与 pydantic 模型字段名一致）

-- ============ user-service ============

CREATE TABLE IF NOT EXISTS users (
    id            TEXT PRIMARY KEY,
    nickname      TEXT NOT NULL,
    gender        TEXT NOT NULL DEFAULT 'hidden',
    region        TEXT NOT NULL DEFAULT 'hidden',
    avatar_url    TEXT,
    mbti_display_type TEXT,
    bio           TEXT,
    is_minor      BOOLEAN NOT NULL DEFAULT FALSE,
    -- privacy 内嵌对象：字段少且总是整体读写，摊平为列而非 jsonb
    allow_nfc_auto_friend_request BOOLEAN NOT NULL DEFAULT TRUE,
    card_visible_to_strangers     BOOLEAN NOT NULL DEFAULT TRUE,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS device_bindings (
    device_uid  TEXT PRIMARY KEY,
    user_id     TEXT NOT NULL,  -- 不设外键：与内存版语义一致（bind 不强制用户已存在），校验留给 service 层
    bound_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    online      BOOLEAN NOT NULL DEFAULT TRUE
);
CREATE INDEX IF NOT EXISTS idx_device_bindings_user ON device_bindings(user_id);

-- ============ pet-profile-service ============

CREATE TABLE IF NOT EXISTS pets (
    id            TEXT PRIMARY KEY,
    user_id       TEXT NOT NULL,  -- 跨服务引用，不做外键（微服务边界）
    name          TEXT NOT NULL,
    e_i           INT NOT NULL DEFAULT 50 CHECK (e_i BETWEEN 0 AND 100),
    s_n           INT NOT NULL DEFAULT 50 CHECK (s_n BETWEEN 0 AND 100),
    t_f           INT NOT NULL DEFAULT 50 CHECK (t_f BETWEEN 0 AND 100),
    j_p           INT NOT NULL DEFAULT 50 CHECK (j_p BETWEEN 0 AND 100),
    avatar_key    TEXT,
    level         INT NOT NULL DEFAULT 1 CHECK (level >= 1),
    growth_points INT NOT NULL DEFAULT 0,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_pets_user ON pets(user_id);

-- ============ social-service ============

CREATE TABLE IF NOT EXISTS friend_requests (
    id          TEXT PRIMARY KEY,
    user_id_a   TEXT NOT NULL,  -- 申请发起方（碰一碰上报方）
    user_id_b   TEXT NOT NULL,
    status      TEXT NOT NULL DEFAULT 'pending'
                CHECK (status IN ('pending', 'accepted', 'rejected')),
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);
-- pending 查重：同一对用户同时只能有一条 pending（无序对，用 LEAST/GREATEST 归一）
CREATE UNIQUE INDEX IF NOT EXISTS uq_friend_requests_pending_pair
    ON friend_requests (LEAST(user_id_a, user_id_b), GREATEST(user_id_a, user_id_b))
    WHERE status = 'pending';
CREATE INDEX IF NOT EXISTS idx_friend_requests_a ON friend_requests(user_id_a) WHERE status = 'pending';
CREATE INDEX IF NOT EXISTS idx_friend_requests_b ON friend_requests(user_id_b) WHERE status = 'pending';

CREATE TABLE IF NOT EXISTS friendships (
    user_id_a   TEXT NOT NULL,  -- 归一约定：user_id_a < user_id_b
    user_id_b   TEXT NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (user_id_a, user_id_b),
    CHECK (user_id_a < user_id_b)
);
CREATE INDEX IF NOT EXISTS idx_friendships_b ON friendships(user_id_b);

-- 碰一碰冷却期由 Redis 承担（key: touch_cooldown:{a}:{b}，EX=冷却秒数），不落 Postgres

-- ============ diary-service ============

CREATE TABLE IF NOT EXISTS diary_entries (
    id               TEXT PRIMARY KEY,
    participant_type TEXT NOT NULL CHECK (participant_type IN ('user_pet', 'town_encounter')),
    pet_id_a    TEXT NOT NULL,
    pet_id_b    TEXT,
    pet_name_a  TEXT NOT NULL,
    pet_name_b  TEXT,
    summary     TEXT NOT NULL,
    mood_tag    TEXT,
    occurred_at TIMESTAMPTZ NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_diary_pet_a ON diary_entries(pet_id_a, occurred_at DESC);
CREATE INDEX IF NOT EXISTS idx_diary_pet_b ON diary_entries(pet_id_b, occurred_at DESC) WHERE pet_id_b IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_diary_occurred ON diary_entries(occurred_at DESC);

-- ============ agent-service/memory-store（预留，当前服务仍为内存实现）============

CREATE TABLE IF NOT EXISTS memory_items (
    id             TEXT PRIMARY KEY,
    pet_id         TEXT NOT NULL,
    kind           TEXT NOT NULL DEFAULT 'episode'
                   CHECK (kind IN ('episode', 'relationship', 'preference')),
    content        TEXT NOT NULL,
    importance     INT NOT NULL DEFAULT 3 CHECK (importance BETWEEN 1 AND 5),
    related_pet_id TEXT,
    created_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_memory_pet ON memory_items(pet_id, created_at DESC);

-- ============ agent-service/memory-store · growth_events (Task 1.6) ============

CREATE TABLE IF NOT EXISTS growth_events (
    id               TEXT PRIMARY KEY,
    pet_id           TEXT NOT NULL,
    dimension        TEXT NOT NULL CHECK (dimension IN ('e_i','s_n','t_f','j_p')),
    delta            INT NOT NULL CHECK (delta BETWEEN -5 AND 5),
    reason           TEXT NOT NULL,
    confidence       NUMERIC(3,2) NOT NULL DEFAULT 0.5 CHECK (confidence BETWEEN 0 AND 1),
    source_memory_ids JSONB NOT NULL DEFAULT '[]'::jsonb,
    trigger          TEXT NOT NULL DEFAULT 'memory_aggregation',
    applied          BOOLEAN NOT NULL DEFAULT FALSE,
    rolled_back      BOOLEAN NOT NULL DEFAULT FALSE,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_growth_pet ON growth_events(pet_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_growth_pet_active ON growth_events(pet_id)
    WHERE applied AND NOT rolled_back;
