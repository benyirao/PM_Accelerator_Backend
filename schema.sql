CREATE TABLE IF NOT EXISTS Temperature_Requests (
    request_id INTEGER PRIMARY KEY AUTOINCREMENT,
    lat REAL NOT NULL,
    lon REAL NOT NULL,
    date_start TEXT NOT NULL,
    date_end TEXT NOT NULL,
    ts TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    city TEXT,
    state TEXT,
    country TEXT
);

-- Temperature is stored in Celsius
CREATE TABLE IF NOT EXISTS Temperatures (
    request_id INTEGER NOT NULL REFERENCES Temperature_Requests(request_id) ON DELETE CASCADE,
    date TEXT NOT NULL,
    min_t REAL NOT NULL,
    max_t REAL NOT NULL,
    PRIMARY KEY (request_id, date)
);

CREATE TABLE IF NOT EXISTS Current_Requests (
    request_id INTEGER PRIMARY KEY AUTOINCREMENT,
    lat REAL NOT NULL,
    lon REAL NOT NULL,
    ts TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    city TEXT,
    state TEXT,
    country TEXT,
    curr_t REAL NOT NULL,
    weather TEXT NOT NULL
)