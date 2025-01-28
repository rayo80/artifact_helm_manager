import os
import subprocess
import requests
import sys

# Constants
ARTIFACT_HUB_API_URL = "https://artifacthub.io/api/v1/packages/search"  # https://artifacthub.io/docs/api/
ARTIFACT_HUB_API_URL_BASE = "https://artifacthub.io/api/v1"
HELM_REPO_ADD_CMD = "helm repo add"
HELM_INSTALL_CMD = "helm install"
HELM_UPGRADE_CMD = "helm upgrade"
HELM_LIST_CMD = "helm list"
HELM_UNINSTALL_CMD = "helm uninstall"
HELM_REPO_REMOVE_CMD = "helm repo remove"


def query_artifact_hub(keyword, num_results=10):
    params = {
        'ts_query_web': keyword,
        'kind': 0,  # 0 - Helm charts, 1 - Falco rules, 2 - OPA policies, etc
        'limit': num_results
    }
    response = requests.get(ARTIFACT_HUB_API_URL, params=params)
    response.raise_for_status()  # Check for request errors
    # print("response", response.json())
    return response.json()['packages']


def display_charts(charts):
    for chart in charts:
        print(f"Name: {chart['name']}")
        print(f"Version: {chart['version']}")
        print(f"Repository: {chart['repository']['name']}")
        print(f"Description: {chart['description'][:100]}...")  # Show a truncated description
        print("-" * 40)


def get_chart_details(repo_name, chart_name):
    # name can be repeated
    response = requests.get(f"{ARTIFACT_HUB_API_URL_BASE}/packages/helm/{repo_name}/{chart_name}")
    response.raise_for_status()
    return response.json()


def add_helm_repo(repo_url):
    val = input("Enter the local reference name: ")
    print(f"Adding Helm repository from {repo_url}...")
    subprocess.run(HELM_REPO_ADD_CMD + " " + val + " " + repo_url, shell=True, check=True)
    subprocess.run("helm repo update", shell=True, check=True)  # Update repo index


def install_or_upgrade_chart(chart_name, release_name, namespace, upgrade=False):
    if upgrade:
        print(f"Upgrading {chart_name} to release {release_name} in {namespace} namespace...")
        subprocess.run([HELM_UPGRADE_CMD, release_name, chart_name, "--namespace", namespace], check=True)
    else:
        print(f"Installing {chart_name} as release {release_name} in {namespace} namespace...")
        subprocess.run([HELM_INSTALL_CMD, release_name, chart_name, "--namespace", namespace], check=True)


def list_deployed_releases(namespace=None):
    cmd = [HELM_LIST_CMD]
    if namespace:
        cmd.extend(["--namespace", namespace])
    subprocess.run(cmd)


def uninstall_release(release_name, cleanup_repo=False):
    print(f"Uninstalling release {release_name}...")
    subprocess.run([HELM_UNINSTALL_CMD, release_name], check=True)
    if cleanup_repo:
        print("Cleaning up Helm repositories...")
        subprocess.run([HELM_REPO_REMOVE_CMD, release_name], check=True)


def main():
    while True:
        print("\nHelm Chart Management")
        print("1. List Available Charts")
        print("2. Get Chart Details")
        print("3. Install/Upgrade Chart")
        print("4. List Deployed Releases")
        print("5. Uninstall a Release")
        print("6. Exit")
        choice = input("Enter your choice: ")

        if choice == "1":
            keyword = input("Enter keyword to search for charts: ")
            charts = query_artifact_hub(keyword)
            display_charts(charts)

        elif choice == "2":
            repo_name = input("Enter the repo name: ")
            chart_name = input("Enter the chart name to get details: ")
            chart_details = get_chart_details(repo_name, chart_name)
            print(f"Name: {chart_details['name']}")
            print(f"Description: {chart_details['description']}")
            print(f"Version: {chart_details['version']}")
            if chart_details.get('maintainers'):
                print(f"Maintainers: {', '.join([m['name'] for m in chart_details.get('maintainers')])}")

            print(f"ID: {chart_details['package_id']}")

            # Add the Helm repository to your system
            add_helm_repo(chart_details['repository']["url"])

        # elif choice == "3":
        #     chart_name = input("Enter the chart name: ")
        #     release_name = input("Enter the release name: ")
        #     namespace = input("Enter the namespace (default 'default'): ") or "default"
        #     upgrade = input("Do you want to upgrade an existing release? (y/n): ").lower() == "y"
        #     install_or_upgrade_chart(chart_name, release_name, namespace, upgrade)
        #
        # elif choice == "4":
        #     namespace = input("Enter the namespace to list releases (or press Enter for all namespaces): ")
        #     list_deployed_releases(namespace or None)
        #
        # elif choice == "5":
        #     release_name = input("Enter the release name to uninstall: ")
        #     cleanup_repo = input("Do you want to clean up the Helm repository as well? (y/n): ").lower() == "y"
        #     uninstall_release(release_name, cleanup_repo)

        elif choice == "6":
            print("Exiting...")
            sys.exit()

        else:
            print("Invalid choice. Please try again.")


if __name__ == "__main__":
    main()
