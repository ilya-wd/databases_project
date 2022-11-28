'''
---------------------------------------------------------------------
Reading & Querying Data sets using dataframes
Revised JAN '21
Sami El-Mahgary /Aalto University
Copyright (c) <2021> <Sami El-Mahgary>
Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.
--------------------------------------------------------------------
ADDITIONAL source for PostgreSQL
-----------------
1. psycopg2 documentation: 
    https://www.psycopg.org/docs/index.html
2. comparing different methods of loading bulk data to postgreSQL:
    https://medium.com/analytics-vidhya/pandas-dataframe-to-postgresql-using-python-part-2-3ddb41f473bd

'''
import psycopg2
from psycopg2 import Error
from sqlalchemy import create_engine, text
import pandas as pd
import numpy as np
from pathlib import Path
import datetime
import openpyxl
import matplotlib.pyplot as plt


# NOTE TO GRADER: IF YOU WANT TO RUN THIS FILE, DON'T FORGET TO INSTALL requirements.txt.
# We added new requirements there and this file might not work without them.

def run_sql_from_file(file_path, conn):
    '''
    Read and run SQL queries from a file at file_path.
    '''
    ok = True
    with open(file_path, 'r') as file:
        sql_cmd = ''
        for line in file:
            i = line.find('--')
            if i != -1:
                line = line[:i]
            line = line.strip()
            if line == '':
                # Empty or comment-only line
                continue

            sql_cmd += ' ' + line
            if line.endswith(';'):
                try:
                    conn.execute(text(sql_cmd))
                except Exception as e:
                    print(f'\nError while executing SQL:\n{e}\n')
                    ok = False
                sql_cmd = ''
    return ok


def main():
    DATADIR = str(Path(__file__).parent.parent)  # for relative path
    print("Data directory: ", DATADIR)

    # In postgres=# shell: CREATE ROLE [role_name] WITH CREATEDB LOGIN PASSWORD '[pssword]'; 
    # https://www.postgresql.org/docs/current/sql-createrole.html

    database = "grp10_vaccinedist"
    user = 'grp10'
    password = 'VeKQ^hLf'
    host = 'dbcourse2022.cs.aalto.fi'
    # use connect function to establish the connection
    try:
        # Connect the postgres database from your local machine using psycopg2
        connection = psycopg2.connect(
            database=database,
            user=user,
            password=password,
            host=host
        )

        # Create a cursor to perform database operations
        cursor = connection.cursor()

        print("PostgreSQL server information")
        print(connection.get_dsn_parameters(), "\n")
        cursor.execute("SELECT version();")
        record = cursor.fetchone()
        print("You are connected to - ", record, "\n")

        # Population of DB with tables:

        # Step 1: Connect to db using SQLAlchemy create_engine
        DIALECT = 'postgresql+psycopg2://'
        db_uri = "%s:%s@%s/%s" % (user, password, host, database)
        print(DIALECT + db_uri)

        engine = create_engine(DIALECT + db_uri)
        psql_conn = engine.connect()

        # NOTE: For some reason, the code for executing queries from an sql file ignores the case,
        # so all tables and attributes in the DB are lower-cased.
        # So, until this is fixed, all columns in dataframes need to be lowercased.


        # Part 3 requirement 1
        dfPatient = pd.read_sql("select * from \"patient\"", psql_conn)
        dfDiagnosis = pd.read_sql("select * from \"diagnosis\"", psql_conn)
        dfReq1 = dfPatient
        dfReq1 = dfReq1[['ssn', 'gender', 'birthday']]
        dfReq1 = dfReq1.merge(dfDiagnosis, left_on='ssn', right_on='patient')
        dfReq1.drop('patient', axis=1, inplace=True)
        dfReq1 = dfReq1.rename(columns={
            'birthday': 'date_of_birth',
            'date': 'diagnosis_date'})
        dfReq1.to_sql('patient_symptoms', con=psql_conn, index=True, if_exists='replace')

        # Part 3 requirement 2
        vacc_patient_df = pd.read_sql("select * from \"vaccine_patient\"", psql_conn)
        vaccine_df = pd.read_sql("select * from \"vaccination_event\"", psql_conn)
        dfBatch = pd.read_sql("select * from \"batch\"", psql_conn)
        dfReq2 = dfPatient
        dfReq2 = dfReq2[['ssn']]
        dfReq2 = dfReq2.merge(vacc_patient_df, left_on='ssn', right_on='patient').drop('patient', axis=1)
        dfReq2 = dfReq2.merge(vaccine_df, on=['date', 'hospital'])
        dfReq2 = dfReq2.merge(dfBatch[['id', 'vaccine_type']], left_on='batch', right_on='id').drop(
            ['hospital', 'batch', 'id'], axis=1)

        dates = pd.DataFrame()
        types = pd.DataFrame()
        grouped = dfReq2.groupby('ssn')
        for i in grouped:
            item = i[1].reset_index(0).drop('index', axis=1).reset_index(0)
            item = item.pivot(index='ssn', columns='index')
            date = item['date'].reset_index(0)
            vacctype = item['vaccine_type'].reset_index(0)
            if 1 not in date:
                date[1] = np.nan
            if 1 not in vacctype:
                vacctype[1] = np.nan
            dates = pd.concat([dates, date])
            types = pd.concat([types, vacctype])

        res = dates.merge(types, on='ssn')
        res.loc[res['0_x'] > res['1_x'], ['0_x', '1_x', '0_y', '1_y']] = res.loc[
            res['0_x'] > res['1_x'], ['1_x', '0_x', '1_y', '0_y']].values
        res = res.rename(columns={
            '0_x': 'date1',
            '1_x': 'date2',
            '0_y': 'vaccine_type1',
            '1_y': 'vaccine_type2'
        })
        missing = dfPatient[~dfPatient['ssn'].isin(res['ssn'])]
        missing = missing[['ssn']]
        missing['date1'] = np.nan
        missing['date2'] = np.nan
        missing['vaccine_type1'] = np.nan
        missing['vaccine_type2'] = np.nan
        res = pd.concat([res, missing])

        res.to_sql('patient_vaccine_info', con=psql_conn, index=True, if_exists='replace')

        # Part 3 requirement 3
        dfPatientSymptoms = pd.read_sql("select * from \"patient_symptoms\"", psql_conn)

        dfSymptomsMales = dfPatientSymptoms[dfPatientSymptoms.gender == 'M']
        dfSymptomsFemales = dfPatientSymptoms[dfPatientSymptoms.gender == 'F']

        topMales = dfSymptomsMales['symptom'].value_counts().index.tolist()[:3]
        topFemales = dfSymptomsFemales['symptom'].value_counts().index.tolist()[:3]

        print("Requirement 3: \n")
        print("Top 3 symptoms for males: \n")
        print(topMales)
        print("\n\nTop 3 symptoms for females: \n")
        print(topFemales)


        # Part 3 requirement 4
        ageValues = ['0-9', '10-19', '20-39', '40-59', '60+']

        now = pd.Timestamp('now')
        dfPAge = dfPatient
        dfPAge.loc[:, 'birthday'] = pd.to_datetime(dfPatient.birthday)
        #dfPAge['birthday'] = pd.to_datetime(dfPAge['birthday'], format='%y%m%d')

        dfPAge['age'] = (now - dfPAge['birthday']).astype('<m8[Y]')

        ageConditions = [
            (dfPAge['age'] < 10),
            (dfPAge['age'] >= 10) & (dfPAge['age'] < 20),
            (dfPAge['age'] >= 20) & (dfPAge['age'] < 39),
            (dfPAge['age'] >= 39) & (dfPAge['age'] < 59),
            (dfPAge['age'] >= 60)
        ]
        dfPAge['age_group'] = np.select(ageConditions, ageValues)

        # removing age column, as it's not required by the task
        dfPAge.drop('age', axis=1, inplace=True)

        print("\n\nRequirement 4: \n")
        print("Patients with age groups: \n")
        print(dfPAge)

        # Part 3 requirement 5
        dfR5vacc_patient = pd.read_sql("select * from \"vaccine_patient\"", psql_conn)
        dfR5patient = dfPAge
        dfR5vacc_patient = dfR5vacc_patient.groupby(['patient'])['date'].count()
        dfR5vacc_patient = dfR5vacc_patient.reset_index()
        dfR5vacc_patient.columns = ['ssn', 'vacc_status']
        dfR5patient = dfR5patient.merge(dfR5vacc_patient, how='left', on='ssn')
        dfR5patient['vacc_status'] = dfR5patient['vacc_status'].fillna(0)
        print("\n\nRequirement 5: \n")
        print("Patients with vaccination status column: \n")
        print(dfR5patient)

        # Part 3 requirement 6
        dfR6patient = dfR5patient.groupby(['age_group'])['ssn'].count()
        dfR6patient = dfR6patient.reset_index()
        dfR6patient.columns = ['age_group', 'total_number']
        dfR6patientVacc_0 = dfR5patient[dfR5patient['vacc_status'] == 0].groupby(['age_group'])['ssn'].count()
        dfR6patientVacc_0 = dfR6patientVacc_0.reset_index()
        dfR6patientVacc_0.columns = ['age_group', '0-vacc']
        dfR6patientVacc_1 = dfR5patient[dfR5patient['vacc_status'] == 1].groupby(['age_group'])['ssn'].count()
        dfR6patientVacc_1 = dfR6patientVacc_1.reset_index()
        dfR6patientVacc_1.columns = ['age_group', '1-vacc']
        dfR6patientVacc_2 = dfR5patient[dfR5patient['vacc_status'] == 2].groupby(['age_group'])['ssn'].count()
        dfR6patientVacc_2 = dfR6patientVacc_2.reset_index()
        dfR6patientVacc_2.columns = ['age_group', '2-vacc']
        dfR6patient = dfR6patient.merge(dfR6patientVacc_0, how='left', on='age_group')
        dfR6patient = dfR6patient.merge(dfR6patientVacc_1, how='left', on='age_group')
        dfR6patient = dfR6patient.merge(dfR6patientVacc_2, how='left', on='age_group')
        dfR6patient.iloc[:, 2:5] = dfR6patient.iloc[:, 2:5].divide(dfR6patient.iloc[:, 1], axis='rows')
        dfR6patient.iloc[:, 2:5] = dfR6patient.iloc[:, 2:5].multiply(100, axis='rows')
        dfR6patient = dfR6patient.drop('total_number', axis=1)
        dfR6patient.rename(columns={'age_group': 'vacc_status'}, inplace=True)
        dfR6patient = dfR6patient.set_index('vacc_status')
        dfR6patient = dfR6patient.T
        print("\n\nRequirement 6: \n")
        print("Patient percentage in each group according to vaccination status: \n")
        print(dfR6patient)

        # Part 3 requirement 7
        dfSymptoms = pd.read_sql("select * from \"symptoms\"", psql_conn)
        query_7 = """
        WITH MAPPING AS
	        (SELECT VACCINE_PATIENT.PATIENT,
			    VACCINATION_EVENT.DATE AS VACC_DATE,
			    VACCINATION_EVENT.HOSPITAL,
			    DIAGNOSIS.SYMPTOM,
			    DIAGNOSIS.DATE AS SYMPTOM_DATE
		    FROM VACCINATION_EVENT
		    JOIN VACCINE_PATIENT ON VACCINE_PATIENT.DATE = VACCINATION_EVENT.DATE
		    AND VACCINE_PATIENT.HOSPITAL = VACCINATION_EVENT.HOSPITAL
		    JOIN DIAGNOSIS ON VACCINE_PATIENT.PATIENT = DIAGNOSIS.PATIENT AND VACCINATION_EVENT.DATE < DIAGNOSIS.DATE),
	    DEDUPLICATED AS
	        (SELECT PATIENT, HOSPITAL, SYMPTOM, SYMPTOM_DATE, MAX(VACC_DATE) AS VACC_DATE
		FROM MAPPING
		GROUP BY PATIENT, HOSPITAL, SYMPTOM, SYMPTOM_DATE)
        SELECT DEDUPLICATED.PATIENT,
	        DEDUPLICATED.HOSPITAL,
	        DEDUPLICATED.SYMPTOM,
	        DEDUPLICATED.SYMPTOM_DATE,
	        DEDUPLICATED.VACC_DATE,
	        BATCH.VACCINE_TYPE
        FROM DEDUPLICATED
        JOIN VACCINATION_EVENT ON VACCINATION_EVENT.DATE = DEDUPLICATED.VACC_DATE
        AND VACCINATION_EVENT.HOSPITAL = DEDUPLICATED.HOSPITAL
        JOIN BATCH ON BATCH.ID = VACCINATION_EVENT.BATCH
        ORDER BY DEDUPLICATED.PATIENT
        """
        result = pd.read_sql_query(query_7, engine)
        df_counts = result.groupby(['vaccine_type', 'symptom']).size().reset_index(name='count')
        vaccine_group = df_counts.groupby(['vaccine_type'])['count'].sum().reset_index(name='total_count')
        df_frequency = pd.merge(df_counts, vaccine_group, left_on='vaccine_type', right_on='vaccine_type', how='left')
        df_frequency['frequency'] = df_frequency.apply(lambda row: row['count'] / row['total_count'], axis=1)
        df_frequency['frequency_text'] = df_frequency.apply(lambda row: 'very common' if row['frequency'] >= 0.1
        else ('common' if row['frequency'] >= 0.05 else 'rare'), axis=1)
        pivot_symptoms = df_frequency.pivot_table(values='frequency_text', index=['symptom'],
                                                  columns='vaccine_type', aggfunc='first').reset_index()
        df_symptom_freq = pd.merge(dfSymptoms, pivot_symptoms, left_on='name', right_on='symptom', how='left')
        df_symptom_freq = df_symptom_freq.drop('symptom', axis=1)
        df_symptom_freq = df_symptom_freq.fillna('-')
        print("\n\nRequirement 7: \n")
        print("Symptoms with their relative frequencies: \n")
        print(df_symptom_freq)

        query_8 = """
                SELECT VACCINE_PATIENT.DATE, VACCINATION_EVENT.HOSPITAL, BATCH.ID, BATCH.NUM_OF_VACC, 
                COUNT(VACCINE_PATIENT.PATIENT) AS NUM_PATIENT
                FROM VACCINE_PATIENT
                JOIN VACCINATION_EVENT ON VACCINE_PATIENT.DATE = VACCINATION_EVENT.DATE
                AND VACCINE_PATIENT.HOSPITAL = VACCINATION_EVENT.HOSPITAL
                JOIN BATCH ON BATCH.ID = VACCINATION_EVENT.BATCH
                GROUP BY VACCINE_PATIENT.DATE, VACCINATION_EVENT.HOSPITAL, BATCH.ID, BATCH.NUM_OF_VACC
                ORDER BY VACCINE_PATIENT.DATE
                        """
        df8_vacc_patient = pd.read_sql_query(query_8, engine)
        df8_vacc_patient["participation"] = round(
            (df8_vacc_patient["num_patient"] / df8_vacc_patient["num_of_vacc"]) * 100, 2)
        atnd_patient = round(df8_vacc_patient['participation'].mean(), 2)
        std = round(df8_vacc_patient["participation"].std(), 2)
        vacc_perc = atnd_patient + std
        print("\n\nRequirement 8: \n")
        print(f"Amount of vaccines that should be reserved for each vaccination to minimize waste is {vacc_perc}%")

        # Part 3, Requirement 9
        query_9_vaccinated = """
            WITH patients AS (
                SELECT vp.patient, MIN(vp.date) AS date
                FROM vaccine_patient as vp
                GROUP BY vp.patient
            )

            SELECT patients.date, COUNT(patients.patient) AS n
            FROM patients
            GROUP BY patients.date
            ORDER BY patients.date
            ;
        """
        dfR9_vaccinated = pd.read_sql_query(query_9_vaccinated, engine)
        dfR9_vaccinated['date'] = pd.to_datetime(dfR9_vaccinated['date'], format='%Y-%m-%d')
        dfR9_vaccinated['n'] = dfR9_vaccinated['n'].cumsum()
        dfR9_vaccinated.set_index(['date'], inplace=True)
        dfR9_vaccinated = dfR9_vaccinated.rename(columns={'n': 'vaccinated'})
        q9_plot = dfR9_vaccinated.plot()

        query_9_full = """
            WITH counts AS (
                SELECT vp.patient, COUNT(vp.patient) AS shots, MAX(vp.date) AS last_date
                FROM vaccine_patient AS vp
                GROUP BY vp.patient
            )

            SELECT counts.last_date AS date, COUNT(counts.patient) as n
            FROM counts
            WHERE counts.shots > 1
            GROUP BY counts.last_date
            ORDER BY counts.last_date ASC
            ;
        """
        dfR9_full = pd.read_sql_query(query_9_full, engine)
        dfR9_full['date'] = pd.to_datetime(dfR9_full['date'], format='%Y-%m-%d')
        dfR9_full['n'] = dfR9_full['n'].cumsum()
        dfR9_full.set_index(['date'], inplace=True)
        dfR9_full = dfR9_full.rename(columns={'n': 'two_vaccines'})

        dfR9_full.plot(ax=q9_plot)#.get_figure().savefig(DATADIR + '/img/part3_req9.png')

        #Uncomment this to see plot, however, doing so will prevent you seeing results of requirement 10
        #plt.show()

        #Part 3, Requirement 10
        query_10 = """
            WITH ve AS (
                -- Vaccination events where worker in question participated
                SELECT ve.hospital, ve.date, vs.weekday
                FROM vaccination_shift AS vs
                RIGHT JOIN vaccination_event AS ve
                ON ve.hospital = vs.hospital AND EXTRACT(isodow FROM ve.date) = (
                    -- Make sure to only include event if weekday matches with
                    -- working shift for the worker in question.
                    CASE vs.weekday
                        WHEN 'Monday' THEN 1
                        WHEN 'Tuesday' THEN 2
                        WHEN 'Wednesday' THEN 3
                        WHEN 'Thursday' THEN 4
                        WHEN 'Friday' THEN 5
                        WHEN 'Saturday' THEN 6
                        WHEN 'Sunday' THEN 7
                    END
                ) AND ve.date >= '2021-05-05' AND ve.date <= '2021-05-15'
                WHERE vs.worker = '19740919-7140'
            )

            -- Patients
            SELECT patient.ssn, patient.name
            FROM ve
            LEFT JOIN vaccine_patient AS vp
            ON vp.hospital = ve.hospital AND vp.date = ve.date
            LEFT JOIN patient
            ON patient.ssn = vp.patient

            UNION

            -- Staff members
            SELECT staff.ssn, staff.name
            FROM ve
            LEFT JOIN vaccination_shift AS vs
            ON vs.hospital = ve.hospital AND vs.weekday = ve.weekday AND vs.worker != '19740919-7140'
            LEFT JOIN staff
            ON staff.ssn = vs.worker
            GROUP BY staff.ssn, staff.name
            ;
        """
        query_10_result = pd.read_sql_query(query_10, engine)
        print("\n\nRequirement 10: \n")
        print("Patients and staff members that the nurse may have met in vaccination events in the past 10 days: \n")
        print(query_10_result)

    except (Exception, Error) as error:
        print("Error while connecting to PostgreSQL", error)
    finally:
        if (connection):
            psql_conn.close()
            connection.close()
            print("PostgreSQL connection is closed")


main()
