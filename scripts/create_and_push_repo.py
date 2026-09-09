"""
Automated GitHub Repository Creator & Pusher
Creates the remote repository 'AAF-Devesh-Version' under your GitHub account via API and pushes the main branch.
"""
import os
import sys
import subprocess
import urllib.request
import json

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

def main():
    repo_name = "AAF-Devesh-Version"
    print("="*80)
    print(f"🚀 AUTOMATED GITHUB REPOSITORY CREATOR & PUSHER")
    print(f"• Target Repository: {repo_name}")
    print("="*80)

    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if not token:
        token = input("🔑 Enter your GitHub Personal Access Token (or press Enter if using GCM browser auth): ").strip()

    if token:
        # Call GitHub REST API to create repository
        url = "https://api.github.com/user/repos"
        payload = json.dumps({
            "name": repo_name,
            "description": "TacticalRMM & ServiceNow Autonomous IT Service Desk (AAF - Devesh Version)",
            "private": False,
            "auto_init": False
        }).encode("utf-8")

        req = urllib.request.Request(url, data=payload, method="POST")
        req.add_header("Authorization", f"token {token}")
        req.add_header("Accept", "application/vnd.github.v3+json")
        req.add_header("User-Agent", "AAF-Automation-Agent")

        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                clone_url = data.get("clone_url")
                print(f"✅ Repository successfully created on GitHub: {data.get('html_url')}")
        except urllib.error.HTTPError as e:
            err_msg = e.read().decode("utf-8", errors="ignore")
            if "already exists" in err_msg:
                print(f"ℹ️ Repository '{repo_name}' already exists on your GitHub account.")
            else:
                print(f"⚠️ GitHub API Response ({e.code}): {err_msg}")
        except Exception as e:
            print(f"⚠️ Error creating repo: {e}")

    # Configure Git Remote
    username = input("\n👤 Enter your GitHub Username (e.g., DeveshPandey14): ").strip()
    if username:
        remote_url = f"https://github.com/{username}/{repo_name}.git"
        if token:
            remote_url = f"https://{token}@github.com/{username}/{repo_name}.git"

        # Remove existing origin if set
        subprocess.run(["git", "remote", "remove", "origin"], capture_output=True)
        subprocess.run(["git", "remote", "add", "origin", remote_url], check=True)
        print(f"🔗 Remote origin set to: https://github.com/{username}/{repo_name}.git")

        print("\n🚀 Pushing 'main' branch to GitHub...")
        res = subprocess.run(["git", "push", "-u", "origin", "main"], capture_output=True, text=True)
        if res.returncode == 0:
            print(f"\n🎉 SUCCESS! Code pushed to: https://github.com/{username}/{repo_name}")
        else:
            print(f"❌ Git Push Error:\n{res.stderr}")

if __name__ == "__main__":
    main()
