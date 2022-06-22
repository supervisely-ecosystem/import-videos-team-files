import os
import init_ui
import globals as g
import supervisely_lib as sly
import moviepy.editor as moviepy
from supervisely_lib.io.fs import get_file_name_with_ext, get_file_ext, get_file_name
from supervisely_lib.video.video import is_valid_ext, ALLOWED_VIDEO_EXTENSIONS


@g.my_app.callback("preview")
@sly.timeit
def preview(api: sly.Api, task_id, context, state, app_logger):
    global file_size
    file_size = {}

    path = state["pathToVideos"]
    try:
        files = api.file.list2(g.TEAM_ID, path)
    except Exception as e:
        g.my_app.show_modal_window("Can not find folder or permission denied. Please, check if path is "
                              "correct or contact tech support", level="warning")
        fields = [
            {"field": "data.tree", "payload": None},
            {"field": "data.connecting", "payload": False},
        ]
        api.task.set_fields(task_id, fields)
        return

    tree_items = []
    for file in files:
        path = os.path.join(state["pathToVideos"], file.name)
        tree_items.append({
            "path": path,
            "size": file.sizeb
        })
        file_size[path] = file.sizeb

    fields = [
        {"field": "data.tree", "payload": tree_items},
        {"field": "data.connecting", "payload": False},
        {"field": "data.started", "payload": False},
    ]
    api.task.set_fields(task_id, fields)


@g.my_app.callback("import_videos")
@sly.timeit
def render_video_from_images(api: sly.Api, task_id, context, state, app_logger):
    selected_pathes = state["selected"]
    videos_pathes = []
    for path in selected_pathes:
        if get_file_ext(path) == '':
            files_infos = api.file.list2(g.TEAM_ID, path)
            curr_video_pathes = [os.path.join(path, file_info.name) for file_info in files_infos]
            videos_pathes.extend(curr_video_pathes)
        else:
            videos_pathes.append(path)

    if len(videos_pathes) == 0:
        g.my_app.show_modal_window("There are no videos to import", "warning")
        sly.logger.warn("nothing to download")
        api.app.set_field(task_id, "data.processing", False)
        return

    project = None
    if state["dstProjectMode"] == "newProject":
        project = api.project.create(g.WORKSPACE_ID, state["dstProjectName"], sly.ProjectType.VIDEOS,
                                     change_name_if_conflict=True)
    elif state["dstProjectMode"] == "existingProject":
        project = api.project.get_info_by_id(state["dstProjectId"])
    if project is None:
        sly.logger.error("Result project is None (not found or not created)")
        return

    dataset = None
    if state["dstDatasetMode"] == "newDataset":
        dataset = api.dataset.create(project.id, state["dstDatasetName"], change_name_if_conflict=True)
    elif state["dstDatasetMode"] == "existingDataset":
        dataset = api.dataset.get_info_by_name(project.id, state["selectedDatasetName"])
    if dataset is None:
        sly.logger.error("Result dataset is None (not found or not created)")
        return

    progress_items_cb = init_ui.get_progress_cb(api, task_id, 1, "Finished", len(videos_pathes))
    vid_count = len(videos_pathes)
    for video_path in videos_pathes:
        if is_valid_ext(get_file_ext(video_path)) is False:
            app_logger.warn(
                'File with extention {} can not be processed. Allowed video extentions {}'.format(get_file_ext(video_path),
                                                                                           ALLOWED_VIDEO_EXTENSIONS))
            progress_items_cb(1)
            vid_count -= 1
            continue

        video_name = get_file_name_with_ext(video_path)
        video_download_path = os.path.join(g.storage_dir, video_name)
        api.file.download(g.TEAM_ID, video_path, video_download_path)

        if get_file_ext(video_name) != g.video_ext:
            new_video_name = get_file_name(video_name) + g.video_ext
            clip = moviepy.VideoFileClip(video_download_path)
            video_download_path = video_download_path.split('.')[0] + g.video_ext
            clip.write_videofile(video_download_path)
            video_name = new_video_name

        file_info = g.api.video.upload_paths(dataset.id, [video_name], [video_download_path])
        progress_items_cb(1)

    init_ui.reset_progress(api, task_id, 1)

    if vid_count > 1:
        g.my_app.show_modal_window(f"{vid_count} videos have been successfully imported to the project \"{project.name}\""
                              f", dataset \"{dataset.name}\". You can continue importing other videos to the same or new "
                              f"project. If you've finished with the app, stop it manually.")
    if vid_count == 1:
        g.my_app.show_modal_window(f"{vid_count} video has been successfully imported to the project \"{project.name}\""
                              f", dataset \"{dataset.name}\". You can continue importing other videos to the same or new "
                              f"project. If you've finished with the app, stop it manually.")

    api.app.set_field(task_id, "data.started", False)
    api.task.set_output_project(task_id, project.id, project.name)


def main():
    sly.logger.info(
        "Script arguments",
        extra={
            "team_id": g.TEAM_ID,
            "workspace_id": g.WORKSPACE_ID,
            "task_id": g.TASK_ID
        }
    )

    data = {}
    state = {}

    init_ui.init_context(data, g.TEAM_ID, g.WORKSPACE_ID)
    init_ui.init(data, state)
    init_ui.init_progress(data,state)
    g.my_app.run(data=data, state=state)


if __name__ == "__main__":
    sly.main_wrapper("main", main)
