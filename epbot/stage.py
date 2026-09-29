"""Handle the `/stage` command in pull request comments.

If the repository owner or a collaborator with write access to the repository comments `/stage` on a pull request,
the bot triggers the workflow static_analysis_clang.yml. The workflow itself creates the check run and manages the
"Staged" label (adds it when it starts, removes it if the run fails), using its own GITHUB_TOKEN.
"""

import gidgethub.routing

router = gidgethub.routing.Router()

STAGE_COMMAND = "/stage"
STAGE_WORKFLOW = "static_analysis_clang.yml"


@router.register("issue_comment", action="created")
async def stage_command(event, gh, *args, **kwargs):
    issue = event.data["issue"]

    # Only handle comments on pull requests, not plain issues.
    if "pull_request" not in issue:
        return

    comment_body = event.data["comment"]["body"].strip()
    if not comment_body.startswith(STAGE_COMMAND):
        return

    commenter = event.data["comment"]["user"]["login"]
    permission = await gh.getitem(
        "/repos/{owner}/{repo}/collaborators/{username}/permission",
        {
            "owner": event.data["repository"]["owner"]["login"],
            "repo": event.data["repository"]["name"],
            "username": commenter,
        },
    )
    if permission["permission"] not in ("admin", "write"):
        return

    pull_request = await gh.getitem(issue["pull_request"]["url"])
    owner = event.data["repository"]["owner"]["login"]
    repo = event.data["repository"]["name"]
    head_sha = pull_request["head"]["sha"]

    await gh.post(
        "/repos/{owner}/{repo}/actions/workflows/{workflow}/dispatches",
        {"owner": owner, "repo": repo, "workflow": STAGE_WORKFLOW},
        data={
            # Must be a ref that exists in this repo; the base branch always does,
            # even for PRs from forks. The exact commit to check out is passed
            # separately as the "ref" input below (pinned to head_sha, not the
            # branch name, so it can't drift if new commits land mid-run).
            "ref": pull_request["base"]["ref"],
            "inputs": {
                "ref": head_sha,
                "pr_number": str(issue["number"]),
            },
        },
    )
