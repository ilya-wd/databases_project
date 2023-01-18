# Helsinki Vaccine Distribution Database - Databases Course Project

This is a course project for Aalto University course Databases (CS-A1153). The goal is creating an PostgreSQL database for vaccine distribution in Helsinki region and doin data analysis on that databases. Tech-stack includes PostgreSQL, Python, NumPy, Pandas, matplotlib. 

This readme is credit of Behram Ulukir.

## Introduction

With the start of the COVID-19 pandemic in 2020, the world entered a new
and catastrophic phase with lockdowns for months. During that time,
research labs around the world were trying to develop vaccines against
the COVID-19 virus. After the approval of the first vaccines from
multiple manufacturers by health authorities, countries then rushed for
vaccinating, thus acquiring and distributing, as many people as
possible. Combined with additional features like vaccine passes and
contact tracing, the vaccination system was requiring a really complex
database that must be able to keep a record of every single thing
related to the vaccination system including patients, transportation
system, staff members, vaccine types, batches, symptoms and diagnosis,
and many more. The complex side was that different parts of this system
must be connected with each other so that a more detailed breakdown can
be reached if required. In this project, as a group of 5 students, we
created a model database for Finland’s vaccination system for Databases
course (CS-A1153).

Along with keeping a record of information related to vaccination, this
database can be used to reach more specific information such as patients
contacted with a specific staff member who tested positive and a staff
member that vaccinated a specific patient, or general statistics such as
the rate of specific symptoms among the receivers of different vaccines
and vaccination rates among different age groups. More examples can be
given, and in fact, during this project, our team analyzed the database
and worked on different aspects of the database.

In the submission, there are 5 files: 2 SQL files, 2 Python files, and 1
text file. The text file, as you can understand from its name, contains
the required libraries for this project. It is highly important to
download those libraries before starting. sqlCreatingDatabase.sql file
contains SQL queries needed to create tables, the sqlPython.py file
contains code to run the sqlCreatingDatabase.sql file and populates the
tables according to the excel sheets given, sqlQueries.sql contains
queries for finding some information about the database and the
databaseAnalysis.py file contains code for analyzing the database. To
create a database from zero, you first need to install the required
libraries, then run the sqlPython.py file. This will automatically
connect to the PostgreSQL server, and create and populate tables
according to the given information.

## Design

![First Version of UML Diagram.](https://github.com/behramulukir/vaccineDistributionHelsinki/blob/main/images/First%20UML.png)

In this first version of the UML diagram, there are 11 different
classes, all of which are connected to each other by a reasonable
relation. By using these relations, we transformed the UML diagram into
a relational model in this way:  
  
Staff (name, phone, birthday, <span class="underline">SSN</span>,
vaccination status, role) - BCNF: both SSN and phone number are unique
attributes thus they are candidate keys, SSN is the primary key. There
isn’t any other unique value except them.  
VaccinationShift (<span class="underline">weekday,
hospital/clinic</span>) - BCNF  
VaccEvent (<span class="underline">Date, hospital/ClinicName,
StaffSSN</span>) - BCNF  
Count (<span class="underline">date, ssID</span>, numberOfPatients) -
BCNF  
Hospital(<span class="underline">name</span>, address, phone) - BCNF:
both name and address are candidate keys, name is the primary key.  
Batch(<span class="underline">batchID</span>, numberOfVacc, vaccType,
prod.Date, exp.Date) - non-BCNF, its decomposed version:
R1(<span class="underline">batchID</span>, numberOfVacc, vaccType,
prod.Date) &  
R2(<span class="underline">vaccType, prod.Date, exp.Date</span>)  
StoredAt(<span class="underline">batchID</span>, HosName) - BCNF  
TransportLog(<span class="underline">batchID, DepDate, ArrDate, DepHos,
ArrHos</span>) - BCNF  
Patient(<span class="underline">ssID</span>, name, birth, gender,
vaccStatus) - BCNF  
SymptomsReported(<span class="underline">ssID, date</span>, name,
isCritical) - BCNF  
VaccType(<span class="underline">vaccID</span>, doses, criticalTemp) -
BCNF  
Manufacturer(<span class="underline">id</span>, origin, contactNumber,
vaccineID) - BCNF: both id and contactNumber are candidate keys, id is
the primary key.

While designing this UML diagram and relational model, we needed to take
some hard decisions. The most important two of them were which
attributes should be considered unique in the class Staff and which
classes are violating BCNF. In the end, we decided that SSN and phone
number should be considered unique and SSN should be the primary key
while the phone number is the candidate key. In this model, we thought
the only class violating BCNF is Batch, therefore we decomposed it into
two. However, the feedback we received and the data given to us led us
to change our UML diagram and relational data.  

![Final UML Diagram.](https://github.com/behramulukir/vaccineDistributionHelsinki/blob/main/images/Final%20UML.png)

Figure [2](#fig:final_uml) is the final version of the UML diagram and
it contains 12 classes. When we transform this UML diagram into a
relational database model which is the baseline for actual SQL database,
we obtained the following model:  
  
staff (<span class="underline">ssn</span>, name, phone, birthday,
vacc\_status, role) - BCNF: both SSN and phone number are unique
attributes thus they are candidate keys, SSN is the primary key. There
isn’t any other unique value except them.  
vaccination\_shift (<span class="underline">hospital, weekday,
worker</span>) - BCNF  
vaccination\_event (<span class="underline">date, hospital</span>,
batch) - BCNF  
vaccine\_patient (<span class="underline">patient, date</span>,
hospital) - BCNF  
hospital(<span class="underline">name</span>, address, phone) - BCNF:
both name and address are candidate keys, name is the primary key  
batch(<span class="underline">id</span>, num\_of\_vacc, vaccine\_type,
manufacturer, prod\_date, exp\_date, hospital) - BCNF  
transport\_log(<span class="underline">batch, dep\_date, arr\_date,
dep\_hos, arr\_hos</span>) - BCNF  
patient(<span class="underline">ssID</span>, name, birth, gender,
vaccStatus) - BCNF  
symptoms(<span class="underline">name</span>, critical) - BCNF  
diagnosis(<span class="underline">patient, symptom, date</span>) -
BCNF  
vaccine\_type(<span class="underline">id</span>, name, doses, temp\_min,
temp\_max) - BCNF  
manufacturer(<span class="underline">id</span>, origin, phone,
vaccine\_type) - BCNF: both id and contactNumber are candidate keys, id
is the primary key  
  
In the relational model above, underlined attributes are primary keys
for the classes they belong to. While some classes have unique
identifiers, ids, as primary keys some classes have multiple attributes
combined as their primary keys. The relational model above is in BCNF
form.

The main difference between two versions of database designs is we first
divided *SymptomsReported* class into two different classes as
*symptoms* and *diagnosis*. This is because the given excel sheet showed
us that storing the data related to symptoms in two different tables is
more logical. The second important change is in the revised version, we
didn’t decompose the *Batch* class because we had learned that it was
already in BCNF form. We also removed *storedAt* class and combined it
with *batch* class. We renamed *count* class as *vaccine\_patient* and
deleted *numberOfPatients* attribute and added *location* attribute. The
*StaffSSN* attribute was changed with *batch* attribute. One general and
very important change we did was standardizing naming. Initially, we
hadn’t decided on a naming convention so members used their own
conventions for it. Later, we decided that this was making writing
queries complex due to different conventions in attribute/class naming.
While working on the second version of our database design, we
standardized naming and used the same naming convention for all
classes/attributes.

## Data Cleaning and Further Improvements

It is generally a good idea to process your data before feeding it into
SQL to avoid feeding erroneous data which may also lead to database
crashes. For this reason, we cleaned the data given to us by using
Python. Pandas framework has very useful tools for that, and we utilized
them when needed. The main purpose of usage was the renaming columns. As
you know, to be able to feed the data frame to the SQL, column names
should match. For that, we renamed columns in our data frame by using
the .rename function. For data cleaning, there were two parts where we
noticed that there is a problem with data. The first one was the
erroneous date inputs in the diagnosis table. One of the inputs was not
in date format and the other one was 2021-02-29, which actually doesn’t
exist. We decided to find them by using the .isinstance function and
drop them since they are apparently breaking the order of the input. The
other field of error was column names in vaccination\_event and
vaccine\_patient tables. Column names in those tables were containing
extra whitespace, so we deleted them by using the .strip() function.

In addition to data cleaning, there is a possible improvement that we
could make. By adding foreign key constraints, we could increase the
efficiency and coherency of our database. Though, it is possible to say
that the current version of the database works enough efficiently for
the scale of given model data.

## Working as a Group

While working as a group, there are two important things: 1. Creating
the right environment 2. Balancing the workload. In this project, we
paid great attention to both of these things and started with choosing a
group leader to take care of the organizational side of things. This
includes distributing roles, creating the environment for group work,
and utilizing tools for collaboration smoother. Our first step in this
was using Google Drive as a common repository and draw.io as a tool for
creating the UML diagram. The second step was using GitLab, as
introduced in the course. While using GitLab and writing code, we had a
general principle: Always write comments about the part you added, so
that other members can understand the function of the code easily. This
principle helped us to have smooth progress, but we also take some
decisions regarding the structure of our code to contribute to that.
This was about writing SQL code by using Python. During the course, we
were introduced to two ways of using SQL code in Python: 1. Running the
SQL file on Python by using a tool given 2. Hardcoding SQL in Python by
using a specific syntax. We chose the first path because in that way it
was easier to keep things under control, and each member was able to
check others’ code easily. So that we spotted mistakes rapidly and fixed
them together.

During the project, we always tried to keep the distribution of roles at
an equal level. For this reason, when we were given the slides about
part 1, we decided to give each member a page of the slide that contains
descriptions of some classes. Each member was responsible for the
classes that were described on the given page. For part 2, we continued
with the same distribution but we also added divided queries needed
according to their difficulties. This means each member was assigned one
or two query, depending on the difficulties of those queries. For part
3, where there are 10 requirements for database analysis, we decided to
give each member 2 requirements, again by taking the difficulties of
requirements into consideration. In this way, we always kept workload
balanced for all members. However, we had a flexible approach to help
other members if needed and acted as a group in required cases.

<div id="tab:schedule">

|       Part 1        | 1.5 weeks for individual work |  1 days for review and documentation  |
| :-----------------: | :---------------------------: | :-----------------------------------: |
|       Part 2        |  2 weeks for individual work  |  2 days for review and documentation  |
|       Part 3        |  2 weeks for indivudual work  |  2 days for review and documentation  |
| Project Deliverable |                               | 1 week for documentation - individual |

Estimated schedule

</div>

The table shows the initial plan for the project. Before
starting to document, we met as a group, discussed and reviewed what we
have done so far for the current part of the project, and solved the
problems that we had. After these meetings, we wrote the documentation,
prepared the submission file, and submitted it.

## Conclusion

Overall, this database is designed to work with model data which is very
very smaller compared to the real vaccination data of Finland. Although
it works quite well with the model data, it would be good to test it
with bigger datasets and see how efficient it is in more real-life-like
situations.

In the future, this database can be expanded and combined with the
database of COVID patients and contact tracing, so for example
quarantine times for people contacted with a COVID-positive person can
be adjusted according to their vaccination status. Also, this would give
healthcare professionals a foresight about the COVID situation in
general.

Overall, this project managed to achieve its aims and now can be used.
It is possible to add new data, write new queries to obtain some
specific data and do analysis on it to learn statistical information
about it.
