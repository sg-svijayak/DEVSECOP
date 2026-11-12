# Todo App

FastAPI + SQLite backend with a tiny static UI.

```bash
pip install -r requirements-dev.txt
uvicorn app.main:app --reload   # http://localhost:8000
pytest
```

## Pipeline (ECS Fargate)

- `ci-cd.yml`: PR runs lint, pytest, pip-audit. Push to `DEV`/`main` also builds the image and scans it with Trivy.
- `deploy-ecs.yml` (reusable): pushes the scanned image to ECR, renders `.aws/task-definition.json`, deploys to the ECS service and waits for stability (circuit-breaker rollback on failure).
- `DEV` deploys to the `dev` GitHub Environment; `main` deploys to `production` (add required reviewers for approval).

### One-time setup per environment
GitHub Environment variables: `AWS_REGION`, `AWS_ROLE_ARN`, `ECR_REPOSITORY`, `ECS_CLUSTER`, `ECS_SERVICE`,
`ECS_TASK_FAMILY`, `TASK_EXECUTION_ROLE_ARN`, `TASK_ROLE_ARN`, `LOG_GROUP`.
AWS: ECR repo, ECS cluster/service (Fargate, behind an ALB, health check `/healthz`), CloudWatch log group, and an
IAM role trusted by GitHub OIDC with ECR push + `ecs:RegisterTaskDefinition/UpdateService/Describe*` + `iam:PassRole`.

> SQLite lives on the container's ephemeral disk: data is lost on redeploy and not shared across tasks.
> Move to RDS/DynamoDB (or EFS) before relying on this beyond a demo.
