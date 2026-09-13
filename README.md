# TrainingDB – Bookingsystem for treningssentre

Et enkelt bookingsystem for gruppetreningstimer (spinning) ved SIT-treningssentrene i Trondheim, bygget med SQLite og Python. Prosjektet demonstrerer databasedesign og forretningslogikk for booking, oppmøte, avbestilling, ventelister og karantene (blacklisting) av brukere.

## Innhold

| Fil | Beskrivelse |
|---|---|
| `TrainingDB.sql` | Databaseskjema (`CREATE TABLE`-setninger med constraints og fremmednøkler) |
| `init.sql` | Testdata som nullstiller og fyller databasen (sentre, aktiviteter, instruktører, brukere, økter og bookinger) |
| `TrainingDB.py` | Python-modul med databaselogikk og en enkel CLI for å teste use case-ene |
| `TrainingDB.db` | SQLite-databasefil generert av `init.sql` |

## Datamodell

Databasen dekker to treningssentre (**Øya treningssenter** og **Dragvoll idrettssenter**) og modellerer:

- **Center / Facility / CenterFacility** – sentre og fasilitetene de tilbyr
- **Room / Bike / Treadmill** – rom (f.eks. sykkelsaler) med utstyr
- **Activity / TrainingSession / Instructor** – aktivitetstyper, konkrete treningsøkter og instruktører
- **SITUser / Booking** – brukere og deres bookinger av økter (status: `booked`, `checked_in`, `no_show`, `cancelled`, `waitlist`)
- **Penalty** – prikker/karantenegrunnlag for sen avbestilling, sen oppmøte eller no-show
- **Club / Membership / RoomReservation** – klubber og romreservasjoner (utvidelse utover kjerne-bookingflyten)
- **OpeningHour / StaffSchedule** – åpningstider og bemanning per senter

Viktige forretningsregler håndheves direkte i skjemaet med `CHECK`-constraints, blant annet:

- En økt kan bare opprettes 48 timer etter `posted_time` (`start_time = datetime(posted_time, '+48 hours')`)
- Et rom kan ikke ha to økter i samme tidsrom (`UNIQUE(room_id, start_time)`)
- En bruker kan ikke booke samme økt flere ganger (`UNIQUE(session_id, email)`)
- En prikk (`Penalty`) utløper alltid 30 dager etter den ble gitt

## Funksjonalitet (use cases) i `TrainingDB.py`

| # | Funksjon | Beskrivelse |
|---|---|---|
| 1 | `init()` | Nullstiller og fyller databasen på nytt fra `init.sql` |
| 2 | `book_training(email, aktivitet, starttid, senter)` | Booker en økt. Sjekker karantene, dobbeltbooking, tidskollisjon med andre bookinger og om økten er full (settes da på venteliste) |
| 3 | `register_attendance(email, aktivitet, starttid, senter)` | Sjekker inn en bruker på en økt. Gir prikk ved sen innsjekking |
| – | `cancel_booking(email, aktivitet, starttid, senter)` | Avbestiller en booking. Gir prikk ved sen avbestilling (< 1 time før start), rykker opp neste på ventelisten, og vurderer karantene |
| – | `update_waitlist(aktivitet, starttid, senter)` | Flytter brukere fra venteliste til bekreftet booking når det blir ledig plass |
| 4 | `week_plan(startdato)` | Skriver ut timeplanen for en gitt uke |
| 5 | `user_history(email, dato)` | Viser en brukers historikk over gjennomførte (innsjekkede) økter |
| 6 | `blacklist(email)` (sammen med `check_attendance`) | Gir prikk for uteblivelse (no-show) og setter brukeren i karantene ved 3+ prikker siste 30 dager |
| 7 | `top_attendees(år-måned)` | Finner bruker(e) med flest innsjekkede økter i en gitt måned |
| 8 | `training_together()` | Finner par av brukere som oftest har trent (sjekket inn) sammen |

## Kom i gang

### Forutsetninger
- Python 3 (bruker kun standardbiblioteket `sqlite3` og `datetime`)

### Kjøre prosjektet

1. Sørg for at `init.sql`, `TrainingDB.py` og `TrainingDB.sql` ligger i samme mappe.
2. Kjør CLI-en:

   ```bash
   python TrainingDB.py
   ```

3. Skriv `init` (eller `1`) for å opprette/nullstille databasen fra `init.sql`.
4. Velg deretter et use case fra menyen, enten med navn (f.eks. `book_training`) eller nummer (`1`–`8`).

Programmet oppretter/bruker filen `TrainingDB.db` i samme mappe som skriptet.

> **Merk:** Dagens dato er hardkodet i koden (`NOW`-konstanten, satt til `2026-03-15 19:00:00`, med noen avvik i enkelte funksjoner) for å gjøre testdataene og use case-ene forutsigbare og reproduserbare.

## Eksempeldata

`init.sql` setter opp:
- 4 brukere (`johnny@stud.ntnu.no` m.fl.)
- 12 instruktører
- 4 spinning-aktiviteter (Spin60, Spin45, Spin 4x4, Spin 8x3)
- Økter fordelt på januar, februar og en full uke i mars 2026
- Bookinger som dekker flere av use case-ene (innsjekket historikk, ventende bookinger, delte økter mellom brukere)
