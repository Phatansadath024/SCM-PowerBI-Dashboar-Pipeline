"""SharePoint helper functions for upload/download of reporting files."""

from pathlib import Path
import os
from dotenv import load_dotenv
from office365.runtime.auth.user_credential import UserCredential
from office365.sharepoint.client_context import ClientContext


def get_sharepoint_context() -> ClientContext:
    """Create SharePoint client context using environment variables."""
    load_dotenv()
    site_url = os.environ["SHAREPOINT_SITE_URL"]
    username = os.environ["SHAREPOINT_USERNAME"]
    password = os.environ["SHAREPOINT_PASSWORD"]

    return ClientContext(site_url).with_credentials(UserCredential(username, password))


def upload_file_from_path(local_path: Path, sharepoint_folder: str) -> None:
    """Upload a local file to a SharePoint document library folder."""
    ctx = get_sharepoint_context()
    folder = ctx.web.get_folder_by_server_relative_url(sharepoint_folder)

    with open(local_path, "rb") as file_obj:
        file_content = file_obj.read()

    folder.upload_file(local_path.name, file_content).execute_query()
    print(f"Uploaded to SharePoint: {local_path.name}")


def download_file(file_name: str, sharepoint_folder: str, local_dir: Path) -> Path:
    """Download a file from SharePoint to a local folder."""
    ctx = get_sharepoint_context()
    local_dir.mkdir(parents=True, exist_ok=True)
    target_path = local_dir / file_name

    file_url = f"{sharepoint_folder}/{file_name}"
    with open(target_path, "wb") as file_obj:
        ctx.web.get_file_by_server_relative_url(file_url).download(file_obj).execute_query()

    print(f"Downloaded from SharePoint: {target_path}")
    return target_path
