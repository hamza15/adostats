# adostats

A python script for performing analysis on Azure DevOps using Azure DevOps Rest API. This script allows you to capture the following information from an Azure DevOps Organization:

- Project Name (multiple projects)
- Repository Name
- Last Update (to a repository)
- Number of branches
- File Count
- Open Pull Requests
- Commits in the last 30 days

## Pre-requisites

Create a Personal Access Token in Azure DevOps with admin permissions

## Usage:

- Install pre-reqs:

``` pip install requests ```

- Set the variables inside analysis.py

- Run:

``` python analysis.py ```
