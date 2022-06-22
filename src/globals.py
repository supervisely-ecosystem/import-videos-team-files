import os
import supervisely_lib as sly


my_app = sly.AppService()
api: sly.Api = my_app.public_api

TEAM_ID = int(os.environ['context.teamId'])
WORKSPACE_ID = int(os.environ['context.workspaceId'])
TASK_ID = int(os.environ["TASK_ID"])

storage_dir = my_app.data_dir
video_ext = '.mp4'
logger = sly.logger
