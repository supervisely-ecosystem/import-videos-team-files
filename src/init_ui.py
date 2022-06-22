import supervisely_lib as sly
from functools import partial


def init_context(data, team_id, workspace_id):
    data["teamId"] = team_id
    data["workspaceId"] = workspace_id


def init(data, state):
    data["started"] = False
    data["finished"] = False
    data["tree"] = False
    data["connecting"] = False

    state["pathToVideos"] = ""
    state["selected"] = ""
    state["checked"] = True

    state["resultingProjectName"] = "my_project"

    state["dstProjectMode"] = "newProject"
    state["dstDatasetMode"] = "newDataset"
    state["dstProjectId"] = None
    state["selectedDatasetName"] = None
    state["dstProjectName"] = "my_project"
    state["dstDatasetName"] = "my_dataset"


def init_progress(data, state):
    data["progressName1"] = None
    data["currentProgressLabel1"] = 0
    data["totalProgressLabel1"] = 0
    data["currentProgress1"] = 0
    data["totalProgress1"] = 0


def reset_progress(api, task_id, index):
    _set_progress(index, api, task_id, None, 0, 0, 0, 0)


def _set_progress(index, api, task_id, message, current_label, total_label, current, total):
    fields = [
        {"field": f"data.progressName{index}", "payload": message},
        {"field": f"data.currentProgressLabel{index}", "payload": current_label},
        {"field": f"data.totalProgressLabel{index}", "payload": total_label},
        {"field": f"data.currentProgress{index}", "payload": current},
        {"field": f"data.totalProgress{index}", "payload": total},
    ]
    api.task.set_fields(task_id, fields)


def _update_progress_ui(api, task_id, progress: sly.Progress, index):
    _set_progress(index, api, task_id, progress.message, progress.current_label, progress.total_label, progress.current, progress.total)


def update_progress(count, index, api: sly.Api, task_id, progress: sly.Progress):
    # hack slight inaccuracies in size convertion
    count = min(count, progress.total - progress.current)
    progress.iters_done(count)
    if progress.need_report():
        progress.report_progress()
        _update_progress_ui(api, task_id, progress, index)

def set_progress(current, index, api: sly.Api, task_id, progress: sly.Progress):
    #if current > progress.total:
    #    current = progress.total
    old_value = progress.current
    delta = current - old_value
    update_progress(delta, index, api, task_id, progress)


def get_progress_cb(api, task_id, index, message, total, is_size=False, func=update_progress):
    progress = sly.Progress(message, total, is_size=is_size)
    progress_cb = partial(func, index=index, api=api, task_id=task_id, progress=progress)
    progress_cb(0)
    return progress_cb
