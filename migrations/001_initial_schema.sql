-- Migration: 001_initial_schema.sql
-- Description: Initial database schema for Roster MCP system
-- Date: 2024-01-14

-- ServiceInfo table: Holds metadata for services
CREATE TABLE IF NOT EXISTS service_infos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date DATE NOT NULL,
    category VARCHAR(50) NOT NULL,
    footnote TEXT,
    skip_service BOOLEAN NOT NULL DEFAULT FALSE,
    skip_reason TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Validate category values
    CONSTRAINT check_category CHECK (category IN ('chinese', 'english', 'sundayschool')),

    -- Ensure skip_reason is provided when service is skipped
    CONSTRAINT check_skip_reason CHECK (
        (skip_service = FALSE AND skip_reason IS NULL) OR
        (skip_service = TRUE AND skip_reason IS NOT NULL)
    )
);

-- Events table: Represents actual service occurrences
CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date DATE NOT NULL,
    service_info_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (service_info_id) REFERENCES service_infos(id)
);

-- Members table: Links people to events with specific roles
CREATE TABLE IF NOT EXISTS members (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id INTEGER NOT NULL,
    role VARCHAR(100) NOT NULL,
    name VARCHAR(200),
    person_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (event_id) REFERENCES events(id) ON DELETE CASCADE,

    -- Ensure at least one identifier is provided
    CONSTRAINT check_identifier CHECK (
        name IS NOT NULL OR person_id IS NOT NULL
    )
);

-- Create indexes for efficient queries
CREATE INDEX IF NOT EXISTS idx_service_infos_date ON service_infos(date);
CREATE INDEX IF NOT EXISTS idx_service_infos_category ON service_infos(category);
CREATE INDEX IF NOT EXISTS idx_events_date ON events(date);
CREATE INDEX IF NOT EXISTS idx_events_service_info ON events(service_info_id);
CREATE INDEX IF NOT EXISTS idx_members_event ON members(event_id);
CREATE INDEX IF NOT EXISTS idx_members_person ON members(person_id);
CREATE INDEX IF NOT EXISTS idx_members_role ON members(role);

-- Create trigger to update the updated_at timestamp
CREATE TRIGGER IF NOT EXISTS update_service_infos_timestamp
    AFTER UPDATE ON service_infos
    FOR EACH ROW
BEGIN
    UPDATE service_infos SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS update_events_timestamp
    AFTER UPDATE ON events
    FOR EACH ROW
BEGIN
    UPDATE events SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS update_members_timestamp
    AFTER UPDATE ON members
    FOR EACH ROW
BEGIN
    UPDATE members SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;