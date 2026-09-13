DELETE FROM Booking;
DELETE FROM TrainingSession;
DELETE FROM Bike;
DELETE FROM Room;
DELETE FROM CenterFacility;

DELETE FROM SITUser;
DELETE FROM Instructor;
DELETE FROM Activity;
DELETE FROM Facility;
DELETE FROM Center;
DELETE FROM Penalty;

INSERT INTO Center(center_id, name, address)
VALUES (1, 'Øya treningssenter','Vangslundsgate 2, 7030 Trondheim'),
	(2, 'Dragvoll idrettssenter','Loholt allé 81, 7049 Trondheim');
	
INSERT INTO Facility(facility_id, type)
VALUES (1, 'Gruppetrening'),(2, 'Egentrening'),(3, 'Utholdenhet'),(4, 'Styrke'),(5, 'Yoga'),
	(6, 'Klatring'),(7, 'Spinning'),(8, 'Hall'),(9, 'Garderober'),(10, 'Badstue'),(11, 'Dusj'),
	(12, 'Ubemannet treningssenter'),(13, 'Squash'),(14, 'Bemannet resepsjon');

INSERT INTO CenterFacility(center_id,facility_id)
VALUES (1,1),(1,2),(1,3),(1,4),(1,5),(1,6),(1,7),(1,8),(1,9),(1,10),(1,11),(1,12),
	(2,2),(2,5),(2,7),(2,8),(2,9),(2,10),(2,11),(2,13),(2,14);
	
INSERT INTO Room(room_id, center_id, name, capacity, type)
VALUES (1, 1,'Sykkelsal', 38, 'Spinningsal'), -- Ut fra bildene ser det ut som samme type sal
	(2, 2, 'Spinningsal', 20, 'Spinningsal');
	
INSERT INTO Bike(room_id, bike_nr, bodybike_function)
VALUES (1,1,1),(1,2,1),(1,3,0),(1,4,0),(1,5,1),(1,6,0),
	(2,1,1),(2,2,1),(2,3,1),(2,4,0),(2,5,0),(2,6,0);
	
INSERT INTO Activity(activity_id, activity_type, name, description)
VALUES (1, 'Spinning','Spin60','En variert spinningtime...'), -- Hentet fra https://www.sit.no/trening/booking?location=trondheim&p=group_trening
	(2, 'Spinning','Spin45','En variert spinningtime...'),
	(3, 'Spinning','Spin 4x4','En forutsigbar intervalltime...'),
	(4, 'Spinning','Spin 8x3','En forutsigbar intervalltime...');
	
INSERT INTO Instructor(instructor_id, first_name)
VALUES (1,'Eirin'),(2,'Siri'),(3,'Jorunn'),(4,'Ramona'),(5,'Trine'),
	(6,'Nora'),(7,'Håkon'),(8,'Hanne'),
	(9,'Ada'),(10,'Sindre'),(11,'Kaja'),(12,'Amalie');

INSERT INTO SITUser(email, first_name, last_name, phone_number, banned_until)
VALUES ('johnny@stud.ntnu.no', 'Johnny', 'Johnnysen', '48761405', NULL), -- +47
	('henrik@stud.ntnu.no', 'Henrik', 'Pettersen', '42783125', NULL),
	('eskil@stud.ntnu.no', 'Eskil A.', 'Skjerve', '94587274', NULL),
	('sondre@stud.ntnu.no', 'Sondre', 'Håkonsen', '99130345', NULL);
	
INSERT INTO TrainingSession(session_id, activity_id, room_id, start_time, end_time, instructor_id, posted_time) -- bruk av KI, skjermbilde for dato
VALUES
-- January
(1, 3, 1, '2026-01-16 07:00:00', '2026-01-16 07:45:00', 1, '2026-01-14 07:00:00'), -- Use case 5
(2, 4, 1, '2026-01-17 07:00:00', '2026-01-17 07:55:00', 6, '2026-01-15 07:00:00'), 
(3, 1, 1, '2026-01-18 16:15:00', '2026-01-18 17:15:00', 6, '2026-01-16 16:15:00'),

-- Febuary
(4, 3, 1, '2026-02-20 07:00:00', '2026-02-20 07:45:00', 1, '2026-02-18 07:00:00'), -- Use case 6
(5, 4, 1, '2026-02-21 07:00:00', '2026-02-21 07:55:00', 6, '2026-02-19 07:00:00'), 
(6, 1, 1, '2026-02-22 16:15:00', '2026-02-22 17:15:00', 6, '2026-02-20 16:15:00'),

-- Monday 16.03.2026
(7, 3, 1, '2026-03-16 07:00:00', '2026-03-16 07:45:00', 1, '2026-03-14 07:00:00'), -- Spin 4x4, Eirin, Øya
(8, 3, 2, '2026-03-16 16:30:00', '2026-03-16 17:15:00', 2, '2026-03-14 16:30:00'), -- Spin 4x4, Siri, Dragvoll
(9, 2, 1, '2026-03-16 16:30:00', '2026-03-16 17:15:00', 3, '2026-03-14 16:30:00'), -- Spin45, Jorunn
(10, 4, 1, '2026-03-16 17:40:00', '2026-03-16 18:35:00', 4, '2026-03-14 17:40:00'), -- Spin 8x3, Ramona
(11, 1, 1, '2026-03-16 19:00:00', '2026-03-16 20:00:00', 5, '2026-03-14 19:00:00'), -- Spin60, Trine

-- Tuesday 17.03.2026
(12, 4, 1, '2026-03-17 07:00:00', '2026-03-17 07:55:00', 6, '2026-03-15 07:00:00'), -- Spin 8x3, Nora
(13, 1, 1, '2026-03-17 18:30:00', '2026-03-17 19:30:00', 7, '2026-03-15 18:30:00'), -- Spin60, Håkon
(14, 3, 1, '2026-03-17 19:45:00', '2026-03-17 20:30:00', 8, '2026-03-15 19:45:00'), -- Spin 4x4, Hanne

-- Wednesday 18.03.2026
(15, 1, 1, '2026-03-18 16:15:00', '2026-03-18 17:15:00', 6, '2026-03-16 16:15:00'), -- Spin60, Nora
(16, 2, 2, '2026-03-18 16:30:00', '2026-03-18 17:15:00', 9, '2026-03-16 16:30:00'), -- Spin45, Ada, Dragvoll
(18, 3, 1, '2026-03-18 17:30:00', '2026-03-18 18:15:00', 10, '2026-03-16 17:30:00'), -- Spin 4x4, Sindre
(19, 2, 1, '2026-03-18 18:30:00', '2026-03-18 19:15:00', 11, '2026-03-16 18:30:00'), -- Spin45, Kaja
(20, 4, 1, '2026-03-18 19:30:00', '2026-03-18 20:25:00', 12, '2026-03-16 19:30:00'); -- Spin 8x3, Amalie

INSERT INTO Booking(booking_id, session_id, email, booking_time, status, showed_up_time, cancelled_time)
VALUES
(1, 1, 'johnny@stud.ntnu.no', '2026-01-15 07:00:00', 'checked_in', '2026-01-16 06:50:00', NULL),
(2, 2, 'johnny@stud.ntnu.no', '2026-01-16 07:00:00', 'checked_in', '2026-01-17 06:50:00', NULL),
(3, 3, 'johnny@stud.ntnu.no', '2026-01-17 16:15:00', 'checked_in', '2026-01-18 16:05:00', NULL),
(4, 1, 'henrik@stud.ntnu.no', '2026-01-15 07:00:00', 'checked_in', '2026-01-16 06:50:00', NULL), -- Use case 8
(5, 2, 'henrik@stud.ntnu.no', '2026-01-16 07:00:00', 'checked_in', '2026-01-17 06:50:00', NULL),
(6, 3, 'henrik@stud.ntnu.no', '2026-01-17 16:15:00', 'checked_in', '2026-01-18 16:05:00', NULL),
(7, 4, 'johnny@stud.ntnu.no', '2026-02-19 07:00:00', 'booked', NULL, NULL), -- Use case 6
(8, 5, 'johnny@stud.ntnu.no', '2026-02-20 07:00:00', 'booked', NULL, NULL),
(9, 6, 'johnny@stud.ntnu.no', '2026-02-21 16:15:00', 'booked', NULL, NULL);