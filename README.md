# Tableau workbook promoter script
Deployment scripts to promote Tableau workbooks between Tableau server environments

## Run

* Set these environment variables:
  - `USERNAME`: Tableau server upper environment username. Needs to have access to the project folder you are deploying workbooks to.
  - `PASSWORD`: Password for the Tableau server upper environment username.
  - `SERVER_URL`: Tableau server upper environment URL.
  - `PROJECT_NAME`: Tableau server project you are deploying workbooks to.
  - `DB_URL`: Upper environment DB hostname.
  - `DB_PORT`: Upper environment DB port.
  - `DB_USER`: Upper environment DB username. Needs to have access to run the queries specified in the Tableau workbook.
  - `DB_PWD`: Upper environment DB password.
  - `DB_NAME`: Upper environment database name.
  
 * You can optionally set the following environment variables:
   - `SKIP_DB_CONNECTION_CHECK`: Skips the database connection and query check that Tableau server runs when a workbook is uploaded.
   - `RUN_AS_JOB`: Runs the upload as an asynchronous job. This would prevent the deployment from having to wait for the db connection check to complete, however the asynchronous job would still check the db connection and fail if it does not work, as opposed to skipping it entirely. You can view the status of the job in the job management section of Tableau server.
   
* To run: `python deploy.py`
