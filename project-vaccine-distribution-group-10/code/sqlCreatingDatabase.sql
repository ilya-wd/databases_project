DROP TABLE IF EXISTS
    batch,
    diagnosis,
    hospital,
    manufacturer,
    patient,
    staff,
    symptoms,
    transport_log,
    vaccination_event,
    vaccination_shift,
    vaccine_patient,
    vaccine_type
CASCADE;

CREATE TABLE vaccine_type (
    id       TEXT NOT NULL,
    name     TEXT NOT NULL,
    doses    INT NOT NULL,
    temp_min INT NOT NULL,
    temp_max INT NOT NULL,

    PRIMARY KEY (id),

    CONSTRAINT positive_doses CHECK (doses > 0),
    CONSTRAINT temp_min_less_than_max CHECK (temp_min < temp_max)
);

CREATE TABLE manufacturer (
    id           TEXT NOT NULL,
    origin       TEXT NOT NULL,
    phone        TEXT NOT NULL,
    vaccine_type TEXT NOT NULL,

    PRIMARY KEY(id),
    FOREIGN KEY(vaccine_type) REFERENCES vaccine_type(id)
);

CREATE TABLE hospital (
    name    TEXT NOT NULL,
    address TEXT NOT NULL,
    phone   TEXT NOT NULL,

    PRIMARY KEY(name)
);

CREATE TABLE batch (
    id           TEXT NOT NULL, 
    num_of_vacc  INT NOT NULL,
    vaccine_type TEXT NOT NULL,
    manufacturer TEXT NOT NULL,
    prod_date    DATE NOT NULL,
    exp_date     DATE NOT NULL,
    hospital     TEXT NOT NULL,

    PRIMARY KEY(id),
    FOREIGN KEY(vaccine_type) REFERENCES vaccine_type(id),
    FOREIGN KEY(hospital) REFERENCES hospital(name),
    FOREIGN KEY(manufacturer) REFERENCES manufacturer(id),

    CONSTRAINT positive_num_of_vacc CHECK(num_of_vacc > 0),
    CONSTRAINT date_prod_less_than_exp CHECK(prod_date < exp_date)
);

CREATE TABLE transport_log (
    batch    TEXT NOT NULL,
    dep_hos  TEXT NOT NULL,
    arr_hos  TEXT NOT NULL,
    dep_date TIMESTAMP NOT NULL,
    arr_date TIMESTAMP NOT NULL,

    PRIMARY KEY(batch, dep_hos, arr_hos, dep_date, arr_date),
    FOREIGN KEY(batch) REFERENCES batch(id),
    FOREIGN KEY(dep_hos) REFERENCES hospital(name),
    FOREIGN KEY(arr_hos) REFERENCES hospital(name)
);

CREATE TABLE staff (
    ssn         TEXT NOT NULL,
    name        TEXT NOT NULL,
    birthday    DATE NOT NULL, 
    phone       TEXT NOT NULL,
    role        TEXT NOT NULL,
    vacc_status BOOL NOT NULL,
    hospital    TEXT NOT NULL,

    PRIMARY KEY(ssn),
    FOREIGN KEY(hospital) REFERENCES hospital(name)
);

CREATE TABLE vaccination_shift (
    hospital TEXT NOT NULL,
    weekday  TEXT NOT NULL,
    worker   TEXT NOT NULL,

    PRIMARY KEY (worker, weekday, hospital),
    FOREIGN KEY(hospital) REFERENCES hospital(name),
    FOREIGN KEY(worker) REFERENCES staff(ssn)
);

CREATE TABLE vaccination_event (
    date     DATE NOT NULL,
    hospital TEXT NOT NULL,
    batch    TEXT NOT NULL,

    PRIMARY KEY(date, hospital),
    FOREIGN KEY(hospital) REFERENCES hospital(name),
    FOREIGN KEY(batch) REFERENCES batch(id)
);

CREATE TABLE patient (
    ssn      TEXT NOT NULL,
    name     TEXT NOT NULL,
    birthday DATE NOT NULL,
    gender   CHAR(1) NOT NULL,

    PRIMARY KEY(ssn)
);

CREATE TABLE vaccine_patient (
    patient  TEXT NOT NULL,
    date     DATE NOT NULL,
    hospital TEXT NOT NULL,

    PRIMARY KEY(patient, date),
    FOREIGN KEY(date, hospital) REFERENCES vaccination_event(date, hospital),
    FOREIGN KEY(patient) REFERENCES patient(ssn),
    FOREIGN KEY(hospital) REFERENCES hospital(name)
);

CREATE TABLE symptoms (
    name     TEXT NOT NULL,
    critical BOOL NOT NULL,

    PRIMARY KEY(name)
);

CREATE TABLE diagnosis (
    patient TEXT NOT NULL,
    symptom TEXT NOT NULL,
    date    DATE NOT NULL,

    PRIMARY KEY(patient, symptom, date),
    FOREIGN KEY(patient) REFERENCES patient(ssn),
    FOREIGN KEY(symptom) REFERENCES symptoms(name)
);
