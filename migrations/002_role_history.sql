-- Migration: 002_role_history.sql
-- Description: Add role_history table for tracking historical role assignments
-- Date: 2025-10-17

-- RoleHistory table: Stores historical role assignments for AI Agent eligibility
CREATE TABLE IF NOT EXISTS role_history (
    role_name TEXT PRIMARY KEY,
    member_ids TEXT NOT NULL,  -- JSON array of member names/ids who have performed this role
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create index for efficient lookups
CREATE INDEX IF NOT EXISTS idx_role_history_updated ON role_history(last_updated);

-- Create trigger to update the updated timestamp
CREATE TRIGGER IF NOT EXISTS update_role_history_timestamp
    AFTER UPDATE ON role_history
    FOR EACH ROW
BEGIN
    UPDATE role_history SET last_updated = CURRENT_TIMESTAMP WHERE role_name = NEW.role_name;
END;
