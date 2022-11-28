-- Query 1
SELECT staff.ssn, staff.name, staff.phone, staff.role, staff.vacc_status, vaccination_shift.hospital
FROM staff, vaccination_event, vaccination_shift
WHERE vaccination_event.date = '2021-05-10' AND vaccination_shift.hospital = vaccination_event.hospital AND vaccination_shift.weekday = 'Monday' AND vaccination_shift.worker = staff.ssn;

-- Query 2
SELECT staff.ssn, staff.name, staff.phone, staff.role, staff.vacc_status, staff.hospital
FROM hospital
LEFT JOIN vaccination_shift as shift
ON shift.hospital = hospital.name AND shift.weekday = 'Wednesday'
RIGHT JOIN staff
ON staff.ssn = shift.worker AND staff.role = 'doctor'
WHERE hospital.address LIKE '%HELSINKI'
ORDER BY ssn ASC;

-- Query 3
--Query 3 part one
WITH LAST_LOG AS
	(SELECT BATCH, MAX(DEP_DATE) AS LAST_DATE
		FROM TRANSPORT_LOG
		GROUP BY BATCH)
SELECT LOG.BATCH,
	LOG.DEP_HOS AS LAST_LOCATION,
	LOG.ARR_HOS AS CURRENT_LOCATION
FROM TRANSPORT_LOG AS LOG
JOIN LAST_LOG ON LOG.BATCH = LAST_LOG.BATCH
AND LOG.DEP_DATE = LAST_LOG.LAST_DATE;
---------------------------------
--Query 3 part two
WITH LAST_LOG AS
	(SELECT BATCH, MAX(DEP_DATE) AS LAST_DATE
		FROM TRANSPORT_LOG
		GROUP BY BATCH)
SELECT LOG.BATCH,
	LOG.ARR_HOS AS LOG_LOCATION,
	BATCH.HOSPITAL AS CORRECT_LOCATION,
	HOSPITAL.PHONE
FROM TRANSPORT_LOG AS LOG
JOIN LAST_LOG ON LOG.BATCH = LAST_LOG.BATCH
AND LOG.DEP_DATE = LAST_LOG.LAST_DATE
JOIN BATCH ON BATCH.ID = LAST_LOG.BATCH
JOIN HOSPITAL ON HOSPITAL.NAME = BATCH.HOSPITAL
WHERE LOG.ARR_HOS != BATCH.HOSPITAL;

-- Query 4
WITH CRITICAL_PATIENTS AS
	(SELECT SSN, PATIENT.NAME
		FROM PATIENT
		JOIN DIAGNOSIS ON PATIENT.SSN = DIAGNOSIS.PATIENT
		JOIN SYMPTOMS ON DIAGNOSIS.SYMPTOM = SYMPTOMS.NAME
		WHERE CRITICAL IS TRUE AND DIAGNOSIS.date > '2021-05-10')
SELECT CRITICAL_PATIENTS.SSN,
	CRITICAL_PATIENTS.NAME,
	BATCH.ID,
	BATCH.VACCINE_TYPE,
	VACCINATION_EVENT.DATE,
	VACCINATION_EVENT.HOSPITAL
FROM CRITICAL_PATIENTS
JOIN VACCINE_PATIENT ON VACCINE_PATIENT.PATIENT = CRITICAL_PATIENTS.SSN
JOIN VACCINATION_EVENT ON VACCINATION_EVENT.HOSPITAL = VACCINE_PATIENT.HOSPITAL
JOIN BATCH ON BATCH.ID = VACCINATION_EVENT.BATCH
ORDER BY SSN;

-- Query 5
CREATE VIEW patient_status AS
SELECT patient.*, COALESCE((COUNT(patient.ssn) >= MIN(vt.doses))::INT, 0) as "vaccinationStatus"
FROM patient
LEFT JOIN vaccine_patient as vp
ON vp.patient = patient.ssn
LEFT JOIN vaccination_event as ve
ON ve.date = vp.date AND ve.hospital = vp.hospital
LEFT JOIN batch
ON batch.id = ve.batch
LEFT JOIN vaccine_type as vt
ON vt.id = batch.vaccine_type
GROUP BY patient.ssn
ORDER BY patient.ssn;

-- Query 6
SELECT hospital.name AS hospital_name, SUM(batch.num_of_vacc) AS total_vaccines, 
SUM(case when vaccine_type='V01' then batch.num_of_vacc else 0 end) as "V01_amount",
SUM(case when vaccine_type='V02' then batch.num_of_vacc else 0 end) as "V02_amount",
SUM(case when vaccine_type='V03' then batch.num_of_vacc else 0 end) as "V03_amount"
FROM batch, hospital
WHERE hospital.name = batch.hospital
GROUP BY hospital.name;


-- Query 7
SELECT total_nums.name, symptom, ROUND( CAST(num_of_symptom AS Numeric)/num_of_patients, 2) AS frequency
FROM (
    SELECT vaccine_type.name, COUNT(DISTINCT vaccine_patient.patient) AS num_of_patients
    FROM vaccine_type, vaccine_patient, vaccination_event, batch
    WHERE vaccine_patient.date = vaccination_event.date
    AND vaccine_patient.hospital = vaccination_event.hospital
    AND batch.id = vaccination_event.batch
    AND batch.vaccine_type = vaccine_type.id
    GROUP BY vaccine_type.name
) AS total_nums, 
(
    SELECT vaccine_type.name, diagnosis.symptom, COUNT(DISTINCT vaccine_patient.patient) AS num_of_symptom
    FROM diagnosis, patient, vaccination_event, vaccine_patient, batch, vaccine_type
    WHERE diagnosis.patient = vaccine_patient.patient
    AND vaccine_patient.date = vaccination_event.date -- DISTINCT at some point? subquery?
    AND vaccine_patient.date <= diagnosis.date
    AND vaccine_patient.hospital = vaccination_event.hospital
    AND batch.id = vaccination_event.batch
    AND (batch.vaccine_type = vaccine_type.id)
    GROUP BY vaccine_type.name, diagnosis.symptom
) AS symptom_nums
WHERE total_nums.name = symptom_nums.name;
