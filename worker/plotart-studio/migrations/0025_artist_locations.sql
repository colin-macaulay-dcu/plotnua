-- PlotArt Studio · migration 0025 · Artist location (Phase C, development 25 Nov 2026)
-- PROPOSAL FOR FOUNDER APPROVAL. NOT RUN against any real database.
-- ADDITIVE: creates ONE new table, artist_locations, and its index, and nothing else. No existing table, row, column or index
-- is touched; no data is inserted; no trigger. artists.county and artists.county_public stay exactly as they are and keep
-- driving today's public profiles until an artist confirms their location (the Studio then writes both).
--
-- What it holds: where the artist is BASED NOW (not birthplace or nationality): country (any, ISO code), the county when
-- based on the island of Ireland (required for Ireland, optional for Northern Ireland, none elsewhere), an optional town or
-- city (never an address), and the delivery areas (local counties and/or nationwide), kept apart from the home county.
-- Nothing is public unless the artist ticks it; public delivery also waits for the founder's privacy-notice switch.
-- The Studio's rules live in src/location.js; these CHECK constraints enforce the same rules in the database.
--
-- Preconditions: migrations up to 0024 have run; the founder has approved this exact file (SHA-256); it runs through
-- studio-d1-migration (restore point and encrypted export first). Re-running it is harmless (IF NOT EXISTS).
-- Rollback (separately approved): DROP TABLE artist_locations;
-- @@DDL-BEGIN (schema.sql carries this block verbatim for new installs and local tests)
CREATE TABLE IF NOT EXISTS artist_locations (
  artist_id TEXT PRIMARY KEY REFERENCES artists(id) ON DELETE CASCADE,
  country TEXT NOT NULL CHECK (length(country) = 2 AND country GLOB '[A-Z][A-Z]'),           -- ISO 3166-1 alpha-2: where the artist is based now
  county TEXT CHECK (county IS NULL OR county IN ('Antrim', 'Armagh', 'Carlow', 'Cavan', 'Clare', 'Cork', 'Derry', 'Donegal', 'Down', 'Dublin', 'Fermanagh', 'Galway', 'Kerry', 'Kildare', 'Kilkenny', 'Laois', 'Leitrim', 'Limerick', 'Longford', 'Louth', 'Mayo', 'Meath', 'Monaghan', 'Offaly', 'Roscommon', 'Sligo', 'Tipperary', 'Tyrone', 'Waterford', 'Westmeath', 'Wexford', 'Wicklow')),
  town TEXT CHECK (town IS NULL OR (length(town) BETWEEN 2 AND 60 AND town NOT GLOB '*[0-9]*')),   -- a town or city, never an address
  delivers_local INTEGER NOT NULL DEFAULT 0 CHECK (delivers_local IN (0, 1)),
  local_counties TEXT NOT NULL DEFAULT '[]' CHECK (json_valid(local_counties) AND json_array_length(local_counties) <= 32),
  delivers_nationwide INTEGER NOT NULL DEFAULT 0 CHECK (delivers_nationwide IN (0, 1)),
  show_location INTEGER NOT NULL DEFAULT 0 CHECK (show_location IN (0, 1)),                -- public only when the artist ticks it
  show_town INTEGER NOT NULL DEFAULT 0 CHECK (show_town IN (0, 1)),
  show_delivery INTEGER NOT NULL DEFAULT 0 CHECK (show_delivery IN (0, 1)),
  confirmed_at TEXT NOT NULL CHECK (length(confirmed_at) BETWEEN 20 AND 30),
  confirmed_by TEXT NOT NULL CHECK (length(confirmed_by) BETWEEN 3 AND 200),                -- 'artist' or the founder's address
  updated_at TEXT NOT NULL CHECK (length(updated_at) BETWEEN 20 AND 30),
  CHECK (country <> 'IE' OR (county IS NOT NULL AND county IN ('Carlow', 'Cavan', 'Clare', 'Cork', 'Donegal', 'Dublin', 'Galway', 'Kerry', 'Kildare', 'Kilkenny', 'Laois', 'Leitrim', 'Limerick', 'Longford', 'Louth', 'Mayo', 'Meath', 'Monaghan', 'Offaly', 'Roscommon', 'Sligo', 'Tipperary', 'Waterford', 'Westmeath', 'Wexford', 'Wicklow'))),                                                  -- based in Ireland: a county is required
  CHECK (country <> 'GB' OR county IS NULL OR county IN ('Antrim', 'Armagh', 'Derry', 'Down', 'Fermanagh', 'Tyrone')),                                -- Northern Ireland: one of its six counties
  CHECK (country IN ('IE', 'GB') OR county IS NULL),                                          -- elsewhere: no county
  CHECK (delivers_local = 1 OR json_array_length(local_counties) = 0),
  CHECK (show_town = 0 OR (show_location = 1 AND town IS NOT NULL))
);
CREATE INDEX IF NOT EXISTS artist_locations_place ON artist_locations(country, county);
-- @@DDL-END
