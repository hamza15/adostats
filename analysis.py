import requests
import csv
from requests.auth import HTTPBasicAuth
from datetime import datetime, timedelta, timezone

# Azure DevOps Configuration
ORGANIZATION = "RCMWMTech"
PAT = "your_personal_access_token"
BASE_URL = f"https://dev.azure.com/{ORGANIZATION}/_apis"
HEADERS = {"Accept": "application/json"}
OUTPUT_FILE = "stats.csv"

auth = HTTPBasicAuth("", PAT)

def get_projects():
    """Fetch all projects in the organization."""
    url = f"{BASE_URL}/projects?api-version=7.1-preview.1"
    response = requests.get(url, auth=auth, headers=HEADERS)
    response.raise_for_status()
    projects = response.json().get("value", [])
    return projects

def get_repositories(project_name):
    """Fetch all repositories in a specific project."""
    url = f"https://dev.azure.com/{ORGANIZATION}/{project_name}/_apis/git/repositories?api-version=7.1-preview.1"
    response = requests.get(url, auth=auth, headers=HEADERS)
    response.raise_for_status()
    repositories = response.json().get("value", [])
    return repositories

def get_repository_metadata(repo_id, project_name):
    """Fetch repository metadata like size and last update time."""
    url = f"https://dev.azure.com/{ORGANIZATION}/{project_name}/_apis/git/repositories/{repo_id}?api-version=7.1-preview.1"
    try:
        response = requests.get(url, auth=auth, headers=HEADERS)
        response.raise_for_status()
        data = response.json()

        # Extract size and last updated time
        size = data.get("size", 0)
        last_updated = data.get("project", {}).get("lastUpdateTime", "Unknown")

        return size, last_updated

    except requests.exceptions.HTTPError as e:
        if response.status_code == 404:
            print(f"Repository '{repo_id}' is archived, disabled, or inaccessible. Skipping...")
            return "Archived/Inaccessible", "Archived/Inaccessible"
        print(f"HTTP Error fetching metadata for repository '{repo_id}': {e}")
        return "Error", "Error"
    except Exception as e:
        print(f"Request Exception for repository '{repo_id}': {e}")
        return "Error", "Error"

def get_branches(repo_id, project_name):
    """Fetch the number of branches in a repository."""
    url = f"https://dev.azure.com/{ORGANIZATION}/{project_name}/_apis/git/repositories/{repo_id}/refs?filter=heads/&api-version=7.1-preview.1"
    response = requests.get(url, auth=auth, headers=HEADERS)
    response.raise_for_status()
    branches = response.json().get("value", [])
    return len(branches)

def get_files(repo_id, project_name):
    """Fetch the number of files in a repository using the count field."""
    url = f"https://dev.azure.com/{ORGANIZATION}/{project_name}/_apis/git/repositories/{repo_id}/items?scopePath=/&recursionLevel=Full&api-version=7.1-preview.1"

    try:
        response = requests.get(url, auth=auth, headers=HEADERS)
        response.raise_for_status()
        data = response.json()

        # Use "count" if available
        file_count = data.get("count")

        # Fallback to counting files from "value" list if "count" is missing
        if file_count is None:
            items = data.get("value", [])
            file_count = len([item for item in items if isinstance(item, dict) and "size" in item])

        return file_count

    except requests.exceptions.HTTPError as e:
        if response.status_code == 404:
            print(f"Repository {repo_id} is empty. No files found.")
            return 0
        print(f"HTTP Error fetching file details for repository {repo_id}: {e}")
        return "Error fetching files"
    except Exception as e:
        print(f"Unexpected error fetching file details for repository {repo_id}: {e}")
        return "Error fetching files"

def get_pull_request_metrics(repo_id, project_name):
    """Fetch the number of open PRs."""
    url = f"https://dev.azure.com/{ORGANIZATION}/{project_name}/_apis/git/pullrequests?repositoryId={repo_id}&api-version=7.1-preview.1"
    response = requests.get(url, auth=auth, headers=HEADERS)
    response.raise_for_status()
    pull_requests = response.json().get("value", [])
    
    open_prs = len([pr for pr in pull_requests if pr["status"] == "active"])
    
    return open_prs

def get_commit_frequency(repo_id, project_name):
    """Analyze commit frequency over the last 30 days."""
    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=30)
    url = (
        f"https://dev.azure.com/{ORGANIZATION}/{project_name}/_apis/git/repositories/{repo_id}/commits?"
        f"searchCriteria.fromDate={start_date.strftime('%Y-%m-%dT%H:%M:%SZ')}&"
        f"searchCriteria.toDate={end_date.strftime('%Y-%m-%dT%H:%M:%SZ')}&api-version=7.1-preview.1"
    )
    response = requests.get(url, auth=auth, headers=HEADERS)
    response.raise_for_status()
    commits = response.json().get("value", [])
    
    return len(commits)

def main():
    print("Fetching projects...")
    projects = get_projects()
    print(f"Found {len(projects)} projects.\n")

    with open(OUTPUT_FILE, mode="w", newline="", encoding="utf-8") as csvfile:
        fieldnames = [
            "Project Name",
            "Repository Name",
            "Repository Size (KB)",
            "Last Updated",
            "Number of Branches",
            "File Count",
            "Open PRs",
            "Commits in last 30 Days"
        ]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        for project in projects:
            project_name = project["name"]
            print(f"Processing project: {project_name}")

            try:
                repositories = get_repositories(project_name)
                if not repositories:
                    writer.writerow({
                        "Project Name": project_name,
                        "Repository Name": "N/A",
                        "Repository Size (KB)": "N/A",
                        "Last Updated": "N/A",
                        "Number of Branches": "N/A",
                        "File Count": "N/A",
                        "Open PRs": "N/A",
                        "Commits in last 30 Days": "N/A"
                    })
                    continue
            except Exception as e:
                print(f"Error fetching repositories for project {project_name}: {e}")
                continue

            for repo in repositories:
                repo_name = repo["name"]
                repo_id = repo["id"]
                print(f"  Repository: {repo_name}")

                # Get repository metadata
                try:
                    size, last_updated = get_repository_metadata(repo_id, project_name)
                except Exception as e:
                    size, last_updated = "Error", "Error"

                # Get branch count
                branch_count = get_branches(repo_id, project_name)

                # Get file count
                file_count = get_files(repo_id, project_name)

                # Get pull request count
                open_prs = get_pull_request_metrics(repo_id, project_name)

                # Get commit frequency
                commit_frequency = get_commit_frequency(repo_id, project_name)

                writer.writerow({
                    "Project Name": project_name,
                    "Repository Name": repo_name,
                    "Repository Size (KB)": f"{size / 1024:.2f}" if isinstance(size, (int, float)) else size,
                    "Last Updated": last_updated,
                    "Number of Branches": branch_count,
                    "File Count": file_count,
                    "Open PRs": open_prs,
                    "Commits in last 30 Days": commit_frequency
                })
                print(f"    Data written to CSV for repository: {repo_name}\n")

if __name__ == "__main__":
    main()
