CREATE TABLE IF NOT EXISTS apple_developer_rss
(
    id          TEXT PRIMARY KEY NOT NULL,
    update_time TEXT
);

INSERT OR IGNORE INTO apple_developer_rss (id, update_time)
VALUES ('RSS_FEED_UPDATE_TIME', NULL);

CREATE TABLE IF NOT EXISTS accessory_ota_update
(
    model       TEXT PRIMARY KEY NOT NULL,
    device_name TEXT,
    update_time TEXT
);

INSERT OR IGNORE INTO accessory_ota_update (model, device_name, update_time)
VALUES ('A2618', 'AirPods Pro 2', NULL);
