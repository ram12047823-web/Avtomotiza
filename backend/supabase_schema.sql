-- Таблица для хранения конфигураций ИИ моделей
CREATE TABLE IF NOT EXISTS ai_models (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    base_url TEXT NOT NULL, -- IP адрес или URL модели
    api_key TEXT, -- Опциональный ключ
    model_type TEXT NOT NULL, -- 'UX', 'Security', 'Performance', 'Accessibility'
    model_name TEXT DEFAULT 'gpt-3.5-turbo', -- Название модели для LiteLLM
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- Индекс для быстрого поиска по типу модели
CREATE INDEX IF NOT EXISTS idx_ai_models_type ON ai_models(model_type);

-- Функция для автоматического обновления updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_ai_models_updated_at
    BEFORE UPDATE ON ai_models
    FOR EACH ROW
    EXECUTE PROCEDURE update_updated_at_column();
