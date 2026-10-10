import argparse
import datetime
import json
import os
import subprocess
import sys
import uuid

def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Automated GitHub contribution generator and activity manager."
    )
    parser.add_argument(
        "--count",
        type=int,
        default=int(os.environ.get("FARM_COMMIT_COUNT", 5)),
        help="Number of contributions to generate in this run."
    )
    parser.add_argument(
        "--author-name",
        type=str,
        default=os.environ.get("FARM_AUTHOR_NAME", "Syqopat"),
        help="Author name for the git commits."
    )
    parser.add_argument(
        "--author-email",
        type=str,
        default=os.environ.get("FARM_AUTHOR_EMAIL", "203693835+Syqopat@users.noreply.github.com"),
        help="Author email for the git commits."
    )
    parser.add_argument(
        "--branch",
        type=str,
        default=os.environ.get("FARM_BRANCH", "main"),
        help="Target git branch to commit and push."
    )
    parser.add_argument(
        "--data-file",
        type=str,
        default="data/activity.json",
        help="Path to activity tracking JSON file."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulate contributions without creating git commits."
    )
    parser.add_argument(
        "--push",
        action="store_true",
        help="Push created commits to remote repository upon completion."
    )
    return parser.parse_args()

def load_activity_data(file_path):
    if not os.path.exists(file_path):
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        return {"total_contributions": 0, "last_run": None, "history": []}
    with open(file_path, "r", encoding="utf-8") as file_handle:
        try:
            return json.load(file_handle)
        except json.JSONDecodeError:
            return {"total_contributions": 0, "last_run": None, "history": []}

def save_activity_data(file_path, data):
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as file_handle:
        json.dump(data, file_handle, indent=2, ensure_ascii=False)
        file_handle.write("\n")

def record_activity_entry(file_path, run_id, index, total):
    data = load_activity_data(file_path)
    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
    data["total_contributions"] = data.get("total_contributions", 0) + 1
    data["last_run"] = now_iso
    data.setdefault("history", []).append({
        "run_id": run_id,
        "entry_index": index,
        "total_in_run": total,
        "timestamp": now_iso
    })
    save_activity_data(file_path, data)
    return data["total_contributions"]

def execute_git(args, env=None):
    process_env = os.environ.copy()
    if env:
        process_env.update(env)
    result = subprocess.run(
        ["git"] + args,
        capture_output=True,
        text=True,
        env=process_env
    )
    if result.returncode != 0:
        raise RuntimeError(f"Git command failed: git {' '.join(args)}\n{result.stderr.strip()}")
    return result.stdout.strip()

def configure_git_identity(author_name, author_email):
    execute_git(["config", "user.name", author_name])
    execute_git(["config", "user.email", author_email])

def create_contributions(count, author_name, author_email, data_file, dry_run=False):
    if count <= 0:
        raise ValueError("Commit count must be greater than zero.")
    run_id = str(uuid.uuid4())
    print(f"Starting contribution run {run_id} with count: {count}")
    if not dry_run:
        configure_git_identity(author_name, author_email)
    git_env = {
        "GIT_AUTHOR_NAME": author_name,
        "GIT_AUTHOR_EMAIL": author_email,
        "GIT_COMMITTER_NAME": author_name,
        "GIT_COMMITTER_EMAIL": author_email
    }
    for index in range(1, count + 1):
        total_so_far = record_activity_entry(data_file, run_id, index, count)
        message = f"chore(farm): update daily activity record [{index}/{count}]"
        if dry_run:
            print(f"[DRY-RUN] Step {index}/{count} | Cumulative: {total_so_far} | {message}")
        else:
            execute_git(["add", data_file])
            execute_git(["commit", "-m", message], env=git_env)
            print(f"Committed {index}/{count} (Total: {total_so_far}): {message}")
    print(f"Successfully processed {count} contribution entries.")

def push_changes(branch):
    print(f"Pushing commits to branch '{branch}'...")
    output = execute_git(["push", "origin", branch])
    print("Push completed successfully.")
    return output

def main():
    args = parse_arguments()
    try:
        create_contributions(
            count=args.count,
            author_name=args.author_name,
            author_email=args.author_email,
            data_file=args.data_file,
            dry_run=args.dry_run
        )
        if args.push and not args.dry_run:
            push_changes(args.branch)
    except Exception as exc:
        print(f"Error executing contribution farm: {exc}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
