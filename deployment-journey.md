
# ✅ Step 1: Create a project, Authenticate and Set Up GCP CLI

### Create a project
<img src="https://github.com/user-attachments/assets/2f393877-e428-4157-a723-224fef3b0495" width="80%" height="80%">

### Authenticate and set your project
```
gcloud auth login
gcloud auth application-default login
gcloud projects list                     # See your projects
gcloud config set project YOUR_PROJECT_ID

gcloud config set project coffee-machine-maintenance  
```

### Enable Required APIs
```
gcloud services enable run.googleapis.com cloudbuild.googleapis.com artifactregistry.googleapis.com containerregistry.googleapis.com iam.googleapis.com cloudresourcemanager.googleapis.com
```

### Set Up Artifact/Container Registry

```
gcloud artifacts repositories create my-repo \
  --repository-format=docker \
  --location=us-central1 \
  --description="My Docker Repo"

gcloud artifacts repositories create coffee-repo --repository-format=docker --location=us-central1 --description="Coffee Machine Repo"
```

<img src="https://github.com/user-attachments/assets/02f50640-e134-491a-9d48-cace8945e996" width="50%" height="50%">

### Authenticate Docker to push to Artifact Registry:
```
gcloud auth configure-docker us-central1-docker.pkg.dev
```

- Replace `us-central1` with your desired region if different

# ✅ Step 2: Push to GitHub

```
cd "1. Set Up"
git init
git remote add origin https://github.com/your-username/your-repo-name.git
git add .
git commit -m "Initial commit"
git push -u origin main
```

```
remote: Permission to adriensieg/coffee-machine.git denied to AdrienDSIEG.
fatal: unable to access ... error: 403
```

![image](https://github.com/user-attachments/assets/f3e9d656-3eaa-4eda-b051-3904f40d890a)

```
ssh-keygen -t ed25519 -C "your-email@example.com"
cat ~/.ssh/id_ed25519.pub
```

![image](https://github.com/user-attachments/assets/3d47b5a6-c3bc-444a-bc06-7f1c8156b6b4)


✅ Fix: Pull the remote changes before pushing
You have two safe options depending on what you want:

- 🔀 Option 1: Merge remote into local: This preserves all commits and is safe if you're collaborating.
```
git pull origin master --rebase
git push -u origin master

```
- 🔀 Option 2: Force push (⚠️ dangerous — overwrites remote): Only use this if you're sure you want your local version to replace what's on GitHub. ** This will delete anything on GitHub that's not in your local repo.**

```
git push -u origin master --force
```


# ✅ Step 3: CI/CD from GitHub → Cloud Build → Cloud Run

### Step 1: Grant Cloud Build permissions to deploy to Cloud Run

#### How to get `[PROJECT_NUMBER]`?

```
gcloud projects describe coffee-machine-maintenance --format="value(projectNumber)"

gcloud projects describe [PROJECT_ID] --format="value(projectNumber)"
```

```
gcloud projects add-iam-policy-binding [PROJECT_ID] \
  --member="serviceAccount:[PROJECT_NUMBER]@cloudbuild.gserviceaccount.com" \
  --role="roles/run.admin"

gcloud projects add-iam-policy-binding [PROJECT_ID] \
  --member="serviceAccount:[PROJECT_NUMBER]@cloudbuild.gserviceaccount.com" \
  --role="roles/iam.serviceAccountUser"


gcloud projects add-iam-policy-binding [PROJECT_ID]
```


```
gcloud projects add-iam-policy-binding coffee-machine-maintenance --member="serviceAccount:425761357703@cloudbuild.gserviceaccount.com" --role="roles/run.admin"

gcloud projects add-iam-policy-binding coffee-machine-maintenance --member="serviceAccount:425761357703@cloudbuild.gserviceaccount.com" --role="roles/iam.serviceAccountUser"

gcloud projects add-iam-policy-binding coffee-machine-maintenance --member="user:siegadrien@gmail.com" --role="roles/run.developer"
```

### Step 2: Create Cloud Build Trigger (manual one-time setup)

- You can do this via the GCP Console under Cloud Build > Triggers, or via CLI:

```
gcloud beta builds triggers create github \
  --name="build-and-deploy" \
  --region=us-central1 \
  --repo-name="[your-repo-name]" \
  --repo-owner="[your-github-username]" \
  --branch-pattern="^main$" \
  --build-config="cloudbuild.yaml"

gcloud beta builds triggers create github --name="build-and-deploy" --region=us-central1 --repo-name="coffee-machine" --repo-owner="adriensieg" --branch-pattern="^master$" --build-config="cloudbuild.yaml"
```











Create a Cloud Run Service (empty for now)

gcloud run deploy my-app \
    --image=us-central1-docker.pkg.dev/[PROJECT_ID]/my-docker-repo/my-app \
    --platform=managed \
    --region=us-central1 \
    --allow-unauthenticated \
    --no-traffic
