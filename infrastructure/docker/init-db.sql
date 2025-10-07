-- Initialize Aquaculture Database

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Create users table
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(100) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE,
    is_superuser BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create fish_species table
CREATE TABLE IF NOT EXISTS fish_species (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    scientific_name VARCHAR(200),
    description TEXT,
    optimal_temperature_min DECIMAL(5,2),
    optimal_temperature_max DECIMAL(5,2),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create models table
CREATE TABLE IF NOT EXISTS models (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL,
    version VARCHAR(50) NOT NULL,
    architecture VARCHAR(100),
    file_path VARCHAR(500),
    accuracy DECIMAL(5,4),
    precision_score DECIMAL(5,4),
    recall_score DECIMAL(5,4),
    f1_score DECIMAL(5,4),
    is_active BOOLEAN DEFAULT FALSE,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by UUID REFERENCES users(id),
    UNIQUE(name, version)
);

-- Create predictions table
CREATE TABLE IF NOT EXISTS predictions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    model_id UUID REFERENCES models(id),
    image_path VARCHAR(500),
    predicted_species_id INTEGER REFERENCES fish_species(id),
    confidence DECIMAL(5,4),
    inference_time_ms INTEGER,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by UUID REFERENCES users(id)
);

-- Create audit_logs table
CREATE TABLE IF NOT EXISTS audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id),
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(100),
    resource_id VARCHAR(255),
    details JSONB,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create api_keys table
CREATE TABLE IF NOT EXISTS api_keys (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id),
    key_hash VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE,
    expires_at TIMESTAMP WITH TIME ZONE,
    last_used_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes
CREATE INDEX idx_predictions_created_at ON predictions(created_at DESC);
CREATE INDEX idx_predictions_model_id ON predictions(model_id);
CREATE INDEX idx_predictions_species_id ON predictions(predicted_species_id);
CREATE INDEX idx_audit_logs_created_at ON audit_logs(created_at DESC);
CREATE INDEX idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_username ON users(username);

-- Insert sample fish species
INSERT INTO fish_species (name, scientific_name, description, optimal_temperature_min, optimal_temperature_max) VALUES
('Bangus', 'Chanos chanos', 'Milkfish - important aquaculture species', 25.0, 32.0),
('Tilapia', 'Oreochromis niloticus', 'Nile tilapia - widely farmed', 20.0, 30.0),
('Catfish', 'Clarias gariepinus', 'African catfish - hardy species', 22.0, 30.0),
('Salmon', 'Salmo salar', 'Atlantic salmon - premium species', 8.0, 14.0),
('Grass Carp', 'Ctenopharyngodon idella', 'Herbivorous carp species', 20.0, 28.0),
('Big Head Carp', 'Hypophthalmichthys nobilis', 'Filter-feeding carp', 18.0, 28.0),
('Silver Carp', 'Hypophthalmichthys molitrix', 'Asian carp species', 18.0, 28.0),
('Indian Carp', 'Labeo rohita', 'Rohu - important in South Asia', 20.0, 30.0),
('Pangasius', 'Pangasianodon hypophthalmus', 'Striped catfish', 24.0, 30.0),
('Gourami', 'Trichogaster pectoralis', 'Snakeskin gourami', 24.0, 30.0)
ON CONFLICT (name) DO NOTHING;

-- Create a default admin user (password: admin123)
-- Note: This should be changed in production!
INSERT INTO users (email, username, hashed_password, full_name, is_superuser) VALUES
('admin@aquaculture.com', 'admin', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYqN8/xKzXu', 'System Administrator', TRUE)
ON CONFLICT (email) DO NOTHING;

-- Grant permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO aquaculture;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO aquaculture;
