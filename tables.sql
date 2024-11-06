CREATE TABLE IF NOT EXISTS users (
    id BIGINT PRIMARY KEY,
    username VARCHAR(64) NOT NULL,
    displayname VARCHAR(64) NOT NULL
);

CREATE TABLE IF NOT EXISTS sessions (
    id SERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(id),
    session_date TIMESTAMP NOT NULL,
    created_date TIMESTAMP NOT NULL,
    duration INT NOT NULL,
    actual_duration INT,
    status INT NOT NULL,
    intention TEXT,
    resolution TEXT,
    is_test BOOLEAN NOT NULL
);