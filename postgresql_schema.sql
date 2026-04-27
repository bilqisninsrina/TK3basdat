CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE role (
    role_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    role_name VARCHAR(50) NOT NULL UNIQUE
);

CREATE TABLE user_account (
    user_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username VARCHAR(100) NOT NULL UNIQUE,
    email VARCHAR(254) NOT NULL UNIQUE,
    full_name VARCHAR(100) NOT NULL DEFAULT '',
    password VARCHAR(255) NOT NULL
);

CREATE TABLE account_role (
    account_role_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    role_id UUID NOT NULL REFERENCES role(role_id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES user_account(user_id) ON DELETE CASCADE,
    CONSTRAINT unique_account_role UNIQUE (role_id, user_id)
);

CREATE TABLE customer (
    customer_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    full_name VARCHAR(100) NOT NULL,
    phone_number VARCHAR(20) NOT NULL,
    user_id UUID NOT NULL UNIQUE REFERENCES user_account(user_id) ON DELETE CASCADE
);

CREATE TABLE organizer (
    organizer_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organizer_name VARCHAR(100) NOT NULL,
    contact_email VARCHAR(254) NOT NULL,
    phone_number VARCHAR(20) NOT NULL DEFAULT '',
    user_id UUID NOT NULL UNIQUE REFERENCES user_account(user_id) ON DELETE CASCADE
);

CREATE TABLE venue (
    venue_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    venue_name VARCHAR(100) NOT NULL,
    capacity INTEGER NOT NULL CHECK (capacity > 0),
    address TEXT NOT NULL,
    city VARCHAR(100) NOT NULL,
    has_reserved_seating BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE TABLE event (
    event_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_datetime TIMESTAMPTZ NOT NULL,
    event_title VARCHAR(200) NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    venue_id UUID NOT NULL REFERENCES venue(venue_id) ON DELETE CASCADE,
    organizer_id UUID NOT NULL REFERENCES organizer(organizer_id) ON DELETE CASCADE
);

CREATE TABLE artist (
    artist_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    genre VARCHAR(100) NOT NULL DEFAULT ''
);

CREATE TABLE event_artist (
    event_artist_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_id UUID NOT NULL REFERENCES event(event_id) ON DELETE CASCADE,
    artist_id UUID NOT NULL REFERENCES artist(artist_id) ON DELETE CASCADE,
    role VARCHAR(100) NOT NULL DEFAULT '',
    CONSTRAINT unique_event_artist UNIQUE (event_id, artist_id)
);

CREATE TABLE ticket_category (
    category_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    category_name VARCHAR(50) NOT NULL,
    quota INTEGER NOT NULL CHECK (quota > 0),
    price NUMERIC(12, 2) NOT NULL CHECK (price >= 0),
    event_id UUID NOT NULL REFERENCES event(event_id) ON DELETE CASCADE
);

CREATE INDEX idx_account_role_user ON account_role(user_id);
CREATE INDEX idx_event_venue ON event(venue_id);
CREATE INDEX idx_event_organizer ON event(organizer_id);
CREATE INDEX idx_event_artist_artist ON event_artist(artist_id);
CREATE INDEX idx_ticket_category_event ON ticket_category(event_id);
