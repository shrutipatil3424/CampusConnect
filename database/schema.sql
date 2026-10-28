-- CampusConnect AI schema (MySQL 8 / MariaDB compatible)
-- The database itself is created automatically by database/db_connection.py (init_db).

CREATE TABLE IF NOT EXISTS students (
    id INT AUTO_INCREMENT PRIMARY KEY,
    full_name VARCHAR(100) NOT NULL,
    email VARCHAR(150) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    college_name VARCHAR(150) NOT NULL,
    course VARCHAR(30) NOT NULL,
    academic_year VARCHAR(20) NOT NULL,
    technical_interests TEXT,
    skills TEXT,
    preferred_categories TEXT,
    career_interests TEXT,
    role ENUM('student', 'admin') NOT NULL DEFAULT 'student',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS events (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    description TEXT NOT NULL,
    category VARCHAR(50) NOT NULL,
    organizer VARCHAR(150) NOT NULL,
    venue VARCHAR(200) NOT NULL,
    mode ENUM('Online', 'Offline', 'Hybrid') NOT NULL DEFAULT 'Offline',
    difficulty ENUM('Beginner', 'Intermediate', 'Advanced') NOT NULL DEFAULT 'Beginner',
    event_date DATETIME NOT NULL,
    registration_deadline DATETIME NOT NULL,
    capacity INT NOT NULL DEFAULT 100,
    fee DECIMAL(8,2) NOT NULL DEFAULT 0,
    tags TEXT,
    target_courses VARCHAR(200) NOT NULL DEFAULT 'All',
    is_active TINYINT(1) NOT NULL DEFAULT 1,
    ai_summary TEXT NULL,
    created_by INT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_events_date (event_date),
    INDEX idx_events_category (category)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS registrations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    event_id INT NOT NULL,
    status ENUM('Registered', 'Attended', 'Cancelled') NOT NULL DEFAULT 'Registered',
    registered_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uq_student_event (student_id, event_id),
    CONSTRAINT fk_reg_student FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
    CONSTRAINT fk_reg_event FOREIGN KEY (event_id) REFERENCES events(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS saved_events (
    student_id INT NOT NULL,
    event_id INT NOT NULL,
    saved_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (student_id, event_id),
    CONSTRAINT fk_saved_student FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
    CONSTRAINT fk_saved_event FOREIGN KEY (event_id) REFERENCES events(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
