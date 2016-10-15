-- Create the user table (for server authentication)
DROP TABLE IF EXISTS user;
CREATE TABLE user
(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  username TEXT NOT NULL,
  password TEXT NOT NULL,
  token TEXT,
  date_created TEXT NOT NULL,
  date_updated TEXT NOT NULL
);


-- Create the job_type table (for cron job types)
DROP TABLE IF EXISTS job_type;
CREATE TABLE job_type
(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  detail TEXT
);
-- Seed the job_type table.
INSERT INTO job_type (id, name, detail)
VALUES (
  NULL,
  'http',
  '{"url":{"type":"string","description":"URL prepended with ''http://''."},"number_of_clones":{"type":"number","description":"Don''t just make the request one time on every interval. Do it X number of times."},"verb":{"type":"string","description":"HTTP verbs: [GET, POST, PUT, DELETE]"},"enable_shadows":{"type":"boolean","description":"Turn on shadows if you want this job to run again even if the last run is still active. (For long running requests.)"}}'
);


-- Create the job table (for cron jobs)
DROP TABLE IF EXISTS job;
CREATE TABLE job
(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL,
  name TEXT NOT NULL,
  type_id INTEGER NOT NULL,
  data TEXT,
  schedule TEXT,
  done INTEGER NOT NULL DEFAULT 0,
  last_ran TEXT,
  date_created TEXT NOT NULL,
  date_updated TEXT NOT NULL,
  FOREIGN KEY(type_id) REFERENCES job_type(id),
  FOREIGN KEY(user_id) REFERENCES user(id),
  UNIQUE(user_id, name)
);

-- Create the job result table (for storing job results)
DROP TABLE IF EXISTS job_result;
CREATE TABLE job_result
(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  job_id INTEGER NOT NULL,
  result TEXT,
  date_created TEXT NOT NULL,
  FOREIGN KEY(job_id) REFERENCES job(id)
)
