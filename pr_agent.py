"""
This is the main script for the Pull Request Review Agent.
It orchestrates the entire process:
1. Parses the PR URL to determine the Git server.
2. Uses the appropriate Git client to fetch PR details.
3. Passes the code changes to the review engine for analysis.
4. Posts the generated feedback back to the pull request.
"""

import sys
import re
from urllib.parse import urlparse

from git_client import get_client
from review_engine import ReviewEngine
from config import GIT_API_TOKENS

def parse_pr_url(url: str):
    """
    Parses a GitHub or GitLab PR URL to extract the server, owner, repo, and PR number.
    
    Args:
        url (str): The full URL of the pull request.
        
    Returns:
        tuple: (server, owner, repo, pr_number) or None if the URL is invalid.
    """
    parsed_url = urlparse(url)
    domain = parsed_url.netloc.lower()
    path_parts = parsed_url.path.strip('/').split('/')

    if "github.com" in domain and len(path_parts) >= 4 and path_parts[2] == "pull":
        server = "github"
        owner = path_parts[0]
        repo = path_parts[1]
        pr_number = int(path_parts[3])
        return server, owner, repo, pr_number
    elif "gitlab.com" in domain and len(path_parts) >= 4 and path_parts[2] == "merge_requests":
        server = "gitlab"
        owner = path_parts[0]
        repo = path_parts[1]
        pr_number = int(path_parts[3])
        return server, owner, repo, pr_number
    # Add more parsers for other servers like Bitbucket
    else:
        print(f"Unsupported or invalid URL: {url}")
        return None

def main():
    """
    Main function to run the PR review agent.
    """
    # Check if a PR URL is provided as a command-line argument.
    if len(sys.argv) < 2:
        print("Usage: python pr_agent.py <pull_request_url>")
        print("Example: python pr_agent.py https://github.com/octocat/Spoon-Knife/pull/1")
        sys.exit(1)

    pr_url = sys.argv[1]
    
    # 1. Parse the URL
    parsed_info = parse_pr_url(pr_url)
    if not parsed_info:
        sys.exit(1)
        
    server, owner, repo, pr_number = parsed_info
    print(f"Reviewing PR #{pr_number} from {server} on {owner}/{repo}")

    # 2. Get the correct Git client
    token = GIT_API_TOKENS.get(server.lower())
    if not token or token == "YOUR_GITHUB_TOKEN_HERE":
        print(f"Error: Missing or placeholder API token for {server}. Please update 'config.py'.")
        sys.exit(1)

    try:
        git_client = get_client(server, token)
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)

    # 3. Fetch PR details
    pr_details = git_client.fetch_pr_details(owner, repo, pr_number)
    if not pr_details:
        print("Failed to fetch PR details. Exiting.")
        sys.exit(1)
    
    print(f"Successfully fetched PR details for '{pr_details['title']}'")
    
    # 4. Analyze code changes
    review_engine = ReviewEngine()
    review_feedback = review_engine.analyze_changes(pr_details['file_changes'])

    # 5. Post the review comment
    print("\n--- Generated Feedback ---")
    print(review_feedback)
    print("\n--------------------------")
    
    confirm = input("Do you want to post this review to the pull request? (yes/no): ").lower()
    if confirm == 'yes':
        git_client.post_review_comment(owner, repo, pr_number, review_feedback)
    else:
        print("Review not posted. Exiting.")

if __name__ == "__main__":
    main()
