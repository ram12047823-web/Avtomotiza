-- Таблица ai_endpoints (бывшая ai_models)
CREATE TABLE IF NOT EXISTS ai_endpoints (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    category TEXT NOT NULL, -- 'UX/UI', 'Security', 'Speed'
    ip_address TEXT NOT NULL, -- Бывшее base_url
    api_key TEXT,
    is_active BOOLEAN DEFAULT true,
    model_name TEXT DEFAULT 'gpt-3.5-turbo',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- Таблица scans (бывшая tests)
CREATE TABLE IF NOT EXISTS scans (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    url TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending', -- 'pending', 'running', 'completed', 'cancelled', 'failed'
    mode TEXT NOT NULL, -- 'Express', 'Standard', 'Deep'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- Таблица scan_reports (бывшая test_results)
CREATE TABLE IF NOT EXISTS scan_reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    scan_id UUID REFERENCES scans(id) ON DELETE CASCADE,
    issue_title TEXT NOT NULL,
    description TEXT,
    severity TEXT DEFAULT 'medium', -- 'low', 'medium', 'high', 'critical'
    screenshot_url TEXT,
    video_url TEXT,
    coordinates JSONB, -- {x, y, w, h}
    fix_suggestion TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- Индексы
CREATE INDEX IF NOT EXISTS idx_ai_endpoints_category ON ai_endpoints(category);
CREATE INDEX IF NOT EXISTS idx_scans_status ON scans(status);
CREATE INDEX IF NOT EXISTS idx_scan_reports_scan_id ON scan_reports(scan_id);

-- Триггеры для updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_ai_endpoints_updated_at
    BEFORE UPDATE ON ai_endpoints
    FOR EACH ROW
    EXECUTE PROCEDURE update_updated_at_column();

CREATE TRIGGER update_scans_updated_at
    BEFORE UPDATE ON scans
    FOR EACH ROW
    EXECUTE PROCEDURE update_updated_at_column();
