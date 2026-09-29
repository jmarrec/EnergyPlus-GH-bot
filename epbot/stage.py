"""Handle the `/stage` command in pull request comments.

If the repository owner or a collaborator with write access to the repository comments `/stage` on a pull request,
the bot should trigger the workflow static_analysis_clang.yml and add the label "Staged" to the pull request.
"""

import gidgethub.routing

router = gidgethub.routing.Router()

STAGE_COMMAND = "/stage"
STAGE_WORKFLOW = "static_analysis_clang.yml"
STAGE_LABEL = "Staged"


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

    # workflow_dispatch doesn't attach itself as a check on the PR, so create the
    # check run ourselves. The workflow updates it to "in_progress"/"completed"
    # using the check_run_id we pass through as an input.
    check_run = await gh.post(
        "/repos/{owner}/{repo}/check-runs",
        {"owner": owner, "repo": repo},
        data={
            "name": "EnergyPlus Static Analysis",
            "head_sha": head_sha,
            "status": "queued",
            "details_url": pull_request["html_url"],
            "output": {
                "title": "EnergyPlus Static Analysis",
                "summary": f"Queued by /stage (comment by @{commenter}).",
            },
        },
    )

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
                "check_run_id": str(check_run["id"]),
            },
        },
    )

    # labels_url is a URI template (e.g. ".../labels{/name}"); strip the template part.
    labels_url = issue["labels_url"].split("{")[0]
    await gh.post(labels_url, {}, data=[STAGE_LABEL])
