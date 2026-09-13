CREATE TABLE Center (
    center_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    address TEXT NOT NULL
);

CREATE TABLE OpeningHour (
	opening_id INTEGER PRIMARY KEY AUTOINCREMENT,
    center_id INTEGER,
    day INTEGER,
    open_hour INTEGER NOT NULL,
    close_hour INTEGER NOT NULL,
    CHECK (day BETWEEN 1 AND 7), -- 1=monday, ..., 7=sunday
    CHECK (open_hour >= 0 AND open_hour < 24),
    CHECK (close_hour > open_hour AND close_hour <= 24),
    FOREIGN KEY (center_id) REFERENCES Center(center_id)
);

CREATE TABLE StaffSchedule (
	schedule_id INTEGER PRIMARY KEY AUTOINCREMENT,
    center_id INTEGER,
    day INTEGER,
    staffing_hour INTEGER NOT NULL,
    close_hour INTEGER NOT NULL,
    CHECK (day BETWEEN 1 AND 7),
    CHECK (staffing_hour >= 0 AND staffing_hour < 24),
    CHECK (close_hour > staffing_hour AND close_hour <= 24),
    FOREIGN KEY (center_id) REFERENCES Center(center_id)
);

CREATE TABLE Facility (
    facility_id INTEGER PRIMARY KEY AUTOINCREMENT,
    type TEXT NOT NULL
);

CREATE TABLE CenterFacility (
    center_id INTEGER,
    facility_id INTEGER,
    PRIMARY KEY (center_id, facility_id),
    FOREIGN KEY (center_id) REFERENCES Center(center_id),
    FOREIGN KEY (facility_id) REFERENCES Facility(facility_id)
);

CREATE TABLE Room (
    room_id INTEGER PRIMARY KEY AUTOINCREMENT,
    center_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    capacity INTEGER NOT NULL,
    type TEXT NOT NULL,
    FOREIGN KEY (center_id) REFERENCES Center(center_id)
);

CREATE TABLE Bike (
    room_id INTEGER NOT NULL,
    bike_nr INTEGER NOT NULL,
    bodybike_function BOOLEAN NOT NULL DEFAULT 0,
    PRIMARY KEY (room_id, bike_nr),
    FOREIGN KEY (room_id) REFERENCES Room(room_id)
);

CREATE TABLE Treadmill (
    room_id INTEGER NOT NULL,
    treadmill_nr INTEGER NOT NULL,
    producer TEXT,
    max_speed REAL,
    max_incline REAL,
    PRIMARY KEY (room_id, treadmill_nr),
    FOREIGN KEY (room_id) REFERENCES Room(room_id)
);

CREATE TABLE Activity (
    activity_id INTEGER PRIMARY KEY AUTOINCREMENT,
    activity_type TEXT NOT NULL,
	name TEXT NOT NULL,
    description TEXT
);

CREATE TABLE TrainingSession (
    session_id INTEGER PRIMARY KEY AUTOINCREMENT,
    activity_id INTEGER NOT NULL,
    room_id INTEGER NOT NULL,
    start_time TEXT NOT NULL, -- formated as (YYYY-MM-DD HH:MM:SS)
    end_time TEXT NOT NULL,
    instructor_id INTEGER NOT NULL,
    posted_time TEXT NOT NULL,
    CHECK (end_time > start_time),
	CHECK (start_time = datetime(posted_time, '+48 hours')), -- changed from DB1
    UNIQUE (room_id, start_time), -- one session per room per timeslot
    FOREIGN KEY (activity_id) REFERENCES Activity(activity_id),
	FOREIGN KEY (instructor_id) REFERENCES Instructor(instructor_id),
    FOREIGN KEY (room_id) REFERENCES Room(room_id)
);

CREATE TABLE Instructor (
	instructor_id INTEGER PRIMARY KEY AUTOINCREMENT,
	first_name TEXT NOT NULL
);

CREATE TABLE SITUser (
    email TEXT PRIMARY KEY,
    first_name TEXT NOT NULL,
	last_name TEXT NOT NULL,
    phone_number TEXT NOT NULL,
	banned_until TEXT
);

CREATE TABLE Booking (
    booking_id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL,
	email TEXT NOT NULL,
    booking_time TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('booked','cancelled','checked_in','no_show','waitlist')),
	showed_up_time TEXT,
	cancelled_time TEXT,
    FOREIGN KEY (email) REFERENCES SITUser(email),
    FOREIGN KEY (session_id) REFERENCES TrainingSession(session_id),
	UNIQUE(session_id, email) -- stop a user from booking the same session multiple times. If a booking is cancelled you can not rebook
);

CREATE TABLE Penalty (
    penalty_id INTEGER PRIMARY KEY AUTOINCREMENT,
	booking_id INTEGER NOT NULL,
    email TEXT NOT NULL,
    date_given TEXT NOT NULL,
    expires_at TEXT NOT NULL,
    reason TEXT,
	CHECK (expires_at = datetime(date_given, '+30 days')),
	FOREIGN KEY (booking_id) REFERENCES Booking(booking_id),
    FOREIGN KEY (email) REFERENCES SITUser(email)
);

CREATE TABLE Club (
    club_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
	description TEXT,
	club_email TEXT
);

CREATE TABLE Membership (
	club_id INTEGER,
	email TEXT,
	PRIMARY KEY (club_id, email),
	FOREIGN KEY (club_id) REFERENCES Club(club_id),
	FOREIGN KEY (email) REFERENCES SITUser(email)
);

CREATE TABLE RoomReservation (
    reservation_id INTEGER PRIMARY KEY AUTOINCREMENT,
    club_id INTEGER NOT NULL,
    room_id INTEGER NOT NULL,
    start_time TEXT NOT NULL,
    end_time TEXT NOT NULL,
	CHECK (start_time >= 0 AND start_time < 24),
    CHECK (end_time > start_time AND end_time <= 24),
    UNIQUE (room_id, start_time),
    FOREIGN KEY (room_id) REFERENCES Room(room_id),
	FOREIGN KEY (club_id) REFERENCES Club(club_id)	
);