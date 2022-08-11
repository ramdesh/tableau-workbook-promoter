import tableauserverclient as TSC
import os
import glob
import logging.config
import re
from typing import List
from typing import Dict

LOG_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "simple": {
            "format": "[%(asctime)s] [%(levelname)s] [%(name)s] "
            "[%(module)s:%(lineno)d] %(message)s"
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": "DEBUG",
            "formatter": "simple",
            "stream": "ext://sys.stdout",
        }
    },
    "loggers": {
        "tableau_workbook_promoter": {
            "level": os.getenv("LOG_LEVEL", "INFO"),
            "handlers": ["console"],
        }
    },
}
logging.config.dictConfig(LOG_CONFIG)
logger = logging.getLogger("tableau_workbook_promoter")


USERNAME = os.environ.get("TABLEAU_USERNAME")
PASSWORD = os.environ.get("TABLEAU_PASSWORD")
SERVER_URL = os.environ.get("TABLEAU_SERVER_URL")
PROJECT_NAME = os.environ.get("TABLEAU_PROJECT", "")
DB_URL = os.environ.get("DB_URL")
DB_PORT = os.environ.get("DB_PORT")
DB_USER = os.environ.get("DB_USERNAME")
DB_PWD = os.environ.get("DB_PASSWORD")
DB_NAME = os.environ.get("DB_NAME")

SKIP_DB_CONNECTION_CHECK = (
    True
    if os.environ.get("SKIP_DB_CONNECTION_CHECK", "false").lower() == "true"
    else False
)
RUN_AS_JOB = True if os.environ.get("RUN_AS_JOB", "false").lower() == "true" else False

SUBSTITUTIONS = {
    "server": DB_URL,
    "port": DB_PORT,
    "dbname": DB_NAME,
}

PATH_TO_WORKBOOK_FILES = "workbooks"

tableau_auth = TSC.TableauAuth(USERNAME, PASSWORD)
server = TSC.Server(SERVER_URL)
server.version = "3.9"


def replace_connection_items(workbook_file: str):
    """
    Replaces connection URLs in the workbook with provider var because Tableau doesn't
    accept new URLs in the request
    :param workbook_file: Path to workbook file
    :return: None
    """
    file_contents = open(workbook_file, "r").read()
    for substitution in SUBSTITUTIONS.keys():
        if SUBSTITUTIONS[substitution] is not None:
            file_contents = re.sub(
                f"{substitution}='(.+?)'",
                f"{substitution}='{SUBSTITUTIONS[substitution]}'",
                file_contents,
            )
    with open(workbook_file, "w") as f:
        f.write(file_contents)


def get_project_id_by_name(
    project_name: str, all_projects: List[Dict[str, str]]
) -> str:
    """
    Evaluates all project list to get project ID for a project identified by name.
    :param project_name: Name of the project.
    :param all_projects: List of all projects available on the server.
    :return: String ID of the project.
    """
    logger.info(f"Getting project Id for project {project_name}")
    return [
        project[project_name] for project in all_projects if project_name in project
    ][0]


def upload_workbooks(
    workbooks_to_be_deployed: List[str],
    project_id: str,
):
    """
    Uploads given list of workbooks to a specified project.
    :param workbooks_to_be_deployed: List of workbooks to be deployed.
    :param project_id: ID of the project the workbooks need to be deployed to.
    :return: None
    """
    if workbooks_to_be_deployed:
        connection_item = TSC.ConnectionItem()
        connection_item.connection_credentials = TSC.ConnectionCredentials(
            name=DB_USER, password=DB_PWD, embed=True
        )
        connection_item.server_address = DB_URL
        connection_item.server_port = DB_PORT
        for workbook in workbooks_to_be_deployed:
            logger.info(f"Uploading workbook {workbook}...")
            wb_item = TSC.WorkbookItem(project_id=project_id)
            logger.info("Replacing URL strings in workbook XML")
            replace_connection_items(workbook)
            logger.info(f"Uploading workbook {workbook}")
            if SKIP_DB_CONNECTION_CHECK:
                logger.info("Skipping database connection checks...")
            if RUN_AS_JOB:
                logger.info("Running deployment as background job...")
            server.workbooks.publish(
                wb_item,
                workbook,
                mode=TSC.Server.PublishMode.Overwrite,
                connections=[connection_item],
                skip_connection_check=SKIP_DB_CONNECTION_CHECK,
                as_job=RUN_AS_JOB,
            )
            logger.info(f"Completed publishing workbook {workbook}.")
    else:
        logger.info("No workbook(s) found to deploy. Exiting the process..")


def publish_workbooks():
    """
    Publishes workbooks to Tableau server.
    """
    logger.info("Signing in to Tableau server...")
    with server.auth.sign_in(tableau_auth):
        all_project_items, pagination_item = server.projects.get()
        all_projects = [{project.name: project.id} for project in all_project_items]
        if not PROJECT_NAME:
            raise ValueError("Project name was not provided.")
        if any(PROJECT_NAME in project for project in all_projects):
            project_id = get_project_id_by_name(PROJECT_NAME, all_projects)
            workbooks_to_be_deployed = glob.glob(PATH_TO_WORKBOOK_FILES + "/*.twb*")
            logger.info(f"Found workbooks: {str(workbooks_to_be_deployed)}")
            upload_workbooks(workbooks_to_be_deployed, project_id)
        else:
            logger.error(f"Project {PROJECT_NAME} not found on server")
            raise ValueError(f"Project {PROJECT_NAME} not found on server")


if __name__ == "__main__":
    try:
        publish_workbooks()
    except Exception as e:
        logger.exception(e)
        raise e
