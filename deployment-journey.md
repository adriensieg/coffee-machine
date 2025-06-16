# Deploy a fully functional multimodal application —powered by a fine-tuned Gemini model— on GCP


- [✅ Step 1: Create a project, Authenticate and Set Up GCP CLI](https://github.com/adriensieg/coffee-machine/blob/master/deployment-journey.md#-step-1-create-a-project-authenticate-and-set-up-gcp-cli)
- [❌ Step 2: Push to GitHub on different branches](https://github.com/adriensieg/coffee-machine/blob/master/deployment-journey.md#-step-2-push-to-github-on-different-branches)
- [❌ Step 3: CI/CD from GitHub → Cloud Build → Cloud Run](https://github.com/adriensieg/coffee-machine/edit/master/deployment-journey.md#-step-3-cicd-from-github--cloud-build--cloud-run)
- [❌ Step 4: Set up an HTTPS load balancer in front of your Cloud Run service](https://github.com/adriensieg/coffee-machine/blob/master/deployment-journey.md#-step-4-set-up-an-https-load-balancer-in-front-of-your-cloud-run-service)
- [❌ Step 5: Easily Fine-Tune Gemini Models (Google Cloud, No Code, for Cheap)](https://github.com/adriensieg/coffee-machine/blob/master/deployment-journey.md#-step-5-easily-fine-tune-gemini-models-google-cloud-no-code-for-cheap)
- [❌ Step 6: Protect my app with Identity Aware Proxy](https://github.com/adriensieg/coffee-machine/blob/master/deployment-journey.md#-step-6-protect-my-app-with-identity-aware-proxy)


## ✅ Step 1: Create a project, Authenticate and Set Up GCP CLI

### A. Authenticate
```
gcloud auth login
gcloud auth application-default login
gcloud projects list                     # See your projects
```
### B. Create a project
```
gcloud projects create PROJECT_ID --name="PROJECT_NAME"
```
Replace:
`PROJECT_ID` with a unique identifier (e.g., my-new-project-123)
`PROJECT_NAME` with a human-readable name (e.g., "My New Project")

Or use the Google Console:

<img src="https://github.com/user-attachments/assets/2f393877-e428-4157-a723-224fef3b0495" width="80%" height="80%">

### C. Set your project
```
gcloud config set project YOUR_PROJECT_ID

gcloud config set project coffee-machine-maintenance  
```

### D. Enable Required APIs
```
gcloud services enable run.googleapis.com cloudbuild.googleapis.com artifactregistry.googleapis.com containerregistry.googleapis.com iam.googleapis.com cloudresourcemanager.googleapis.com
```

### E. Set Up Artifact/Container Registry

```
gcloud artifacts repositories create my-repo \
  --repository-format=docker \
  --location=us-central1 \
  --description="My Docker Repo"

gcloud artifacts repositories create coffee-repo --repository-format=docker --location=us-central1 --description="Coffee Machine Repo"
```

<img src="https://github.com/user-attachments/assets/02f50640-e134-491a-9d48-cace8945e996" width="50%" height="50%">

### F. Authenticate Docker to push to Artifact Registry:
```
gcloud auth configure-docker us-central1-docker.pkg.dev
```

- Replace `us-central1` with your desired region if different

## ❌ Step 2: Push to GitHub on different branches

```
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


# ❌ Step 3: CI/CD from GitHub → Cloud Build → Cloud Run

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
gcloud beta builds connections create github github-connection --region=us-central1
```

![image](https://github.com/user-attachments/assets/a1d52c1c-87b8-4149-b2e3-52f9e77c7a3e)

👉 Enable Secret Manager API. Wait 1–2 minutes after enabling.
Then we have to grant `secretmanager.admin` to our Cloud Build service account `secretmanager.secrets.create` and `secretmanager.secrets.setIamPolicy` are both included in the `roles/secretmanager.admin` role, which is exactly what we want to assign to the Cloud Build service account (called a P4SA, or "Project-for-Service-Account").
```
gcloud projects add-iam-policy-binding coffee-machine-maintenance --member="serviceAccount:service-425761357703@gcp-sa-cloudbuild.iam.gserviceaccount.com" --role="roles/secretmanager.admin"
```

```
gcloud beta builds connections list --region=us-central1
```

![image](https://github.com/user-attachments/assets/00d4429b-be88-4af3-be4e-7c4d4d29597f)

- Go to https://console.cloud.google.com/cloud-build/connections?project=coffee-machine-maintenance
- Click your connection name (github-connection)
- Click "Install GitHub App"
- Grant access to your GitHub repo (e.g. coffee-machine)
- Complete the OAuth authorization

![image](https://github.com/user-attachments/assets/cdd44781-7e5e-44ac-bbff-5a8222653c70)

Then 
![image](https://github.com/user-attachments/assets/a83a584b-6d5f-48b6-93d1-49bfd901fc5e)

OR 
```
gcloud beta builds repositories create coffee-machine \
  --repository-format=github \
  --connection=projects/PROJECT_ID/locations/us-central1/connections/github-1 \
  --remote-uri=https://github.com/adriensieg/coffee-machine \
  --region=us-central1

gcloud beta builds triggers create github \
  --name="build-and-deploy" \
  --region=us-central1 \
  --repo-name="[your-repo-name]" \
  --repo-owner="[your-github-username]" \
  --branch-pattern="^main$" \
  --build-config="cloudbuild.yaml"
```

```
gcloud beta builds repositories create coffee-machine --repository-format=github --connection=projects/coffee-machine-maintenance/locations/us-central1/connections/github-1 --remote-uri=https://github.com/adriensieg/coffee-machine --region=us-central1

gcloud beta builds triggers create github --name="build-and-deploy" --region=us-central1 --repo-name="coffee-machine" --repo-owner="adriensieg" --branch-pattern="^master$" --build-config="cloudbuild.yaml"


gcloud beta builds triggers create github --name="build-and-deploy" --region=us-central1 --repository="coffee-machine" --branch-pattern="^master$" --build-config="cloudbuild.yaml" --connection="projects/coffee-machine-maintenance/locations/us-central1/connections/github-connection"

```



gcloud beta builds connections create github --region=us-central1 --github-owner=adriensieg --repository=coffee-machine --name=github-connection


Create a Cloud Run Service (empty for now)

gcloud run deploy my-app \
    --image=us-central1-docker.pkg.dev/[PROJECT_ID]/my-docker-repo/my-app \
    --platform=managed \
    --region=us-central1 \
    --allow-unauthenticated \
    --no-traffic


git pull origin master --rebase
git add .
git commit -m "Initial commit"
git push -u origin master






# ✅ Step 4: Set up an HTTPS load balancer in front of your Cloud Run service

Key Components to create: 
- **Static IP**: coffee-machine-lb-ip - Your global static IP address
- **Network Endpoint Group**: `coffee-machine-neg` - Points to your Cloud Run service
- **Backend Service**: `coffee-machine-backend` - Routes traffic to your NEG
- **URL Map**: `coffee-machine-url-map` - Defines routing rules
- **SSL Certificate**: `coffee-machine-ssl-cert` - Managed SSL certificate
- **HTTPS Proxy**: `coffee-machine-https-proxy` - Handles HTTPS traffic
- **Forwarding Rules**: Routes traffic from the static IP to your service

### Set your project
```
gcloud config set project coffee-machine-maintenance
```
### Enable required APIs
```
gcloud services enable compute.googleapis.com
gcloud services enable certificatemanager.googleapis.com
```

### 1. Reserve a static IP address
```
gcloud compute addresses create coffee-machine-lb-ip --global
```

###  Get the reserved IP (save this for DNS setup)
```
gcloud compute addresses describe coffee-machine-lb-ip --global --format="value(address)"
```
###  2. Create a Network Endpoint Group (NEG) for your Cloud Run service
```
gcloud compute network-endpoint-groups create coffee-machine-neg --region=us-central1 --network-endpoint-type=serverless --cloud-run-service=iap-protected-app-425761357703
```

###  3. Create a backend service
```
gcloud compute backend-services create coffee-machine-backend --global
```

###  4. Add the NEG to the backend service
```
gcloud compute backend-services add-backend coffee-machine-backend --global --network-endpoint-group=coffee-machine-neg --network-endpoint-group-region=us-central1
```

###  5. Create a URL map
```
gcloud compute url-maps create coffee-machine-url-map --default-service=coffee-machine-backend
```

###  6. Create a managed SSL certificate (replace YOUR_DOMAIN with your actual domain)
You'll need to point your domain to the static IP before this certificate validates
```
gcloud compute ssl-certificates create coffee-machine-ssl-cert --domains=pretotype.live --global
```

#### Create a DNS Zone
![image](https://github.com/user-attachments/assets/b46e3345-3b72-46ba-9bb4-86fb4d6c8ff5)

#### Create a CNAME
![image](https://github.com/user-attachments/assets/604271fa-d061-4dff-9a69-2b4b5625481c)

#### Associate the DNS to the IP addres
![image](https://github.com/user-attachments/assets/23b8ebed-878a-4065-b118-512b30fb7b34)

#### Change the DNS in GoDaddy
![image](https://github.com/user-attachments/assets/135b6650-76a3-4594-8b02-aa213262d311)

![image](https://github.com/user-attachments/assets/01d06ebc-41b1-4017-871d-b2743db48794)

### 7. Create an HTTPS proxy
```
gcloud compute target-https-proxies create coffee-machine-https-proxy --url-map=coffee-machine-url-map --ssl-certificates=coffee-machine-ssl-cert
```

### 8. Create a global forwarding rule for HTTPS (port 443)
```
gcloud compute forwarding-rules create coffee-machine-https-rule --global --target-https-proxy=coffee-machine-https-proxy --address=coffee-machine-lb-ip --ports=443
```


### Optional: Create HTTP to HTTPS redirect
#### 9a. Create HTTP URL map for redirect
```
gcloud compute url-maps create coffee-machine-http-redirect --default-url-redirect-response-code=301 --default-url-redirect-https-redirect
```
#### 9b. Create HTTP proxy
gcloud compute target-http-proxies create coffee-machine-http-proxy \
    --url-map=coffee-machine-http-redirect

#### 9c. Create HTTP forwarding rule
gcloud compute forwarding-rules create coffee-machine-http-rule \
    --global \
    --target-http-proxy=coffee-machine-http-proxy \
    --address=coffee-machine-lb-ip \
    --ports=80

#### 🎯 At the end - I want to achieve that: 

![image](https://github.com/user-attachments/assets/dd16ead6-d33a-4b0d-9731-e4ca250162b7)

![image](https://github.com/user-attachments/assets/2449307e-3087-4c23-ae9f-96de5d68e18b)


# ❌ Step 5: Easily Fine-Tune Gemini Models (Google Cloud, No Code, for Cheap)

https://www.youtube.com/watch?v=6UfFq7IvjVA
https://cloud.google.com/vertex-ai/generative-ai/docs/models/gemini-use-supervised-tuning#vertex-ai-sdk-for-python_1

# ❌ Step 6: Protect my app with Identity Aware Proxy

![image](https://github.com/user-attachments/assets/e3221c44-ec95-4894-8b80-288aaf745b11)


![image](https://github.com/user-attachments/assets/6bd9be01-d324-45ac-b24c-f45b2ef5a119)



![image](https://github.com/user-attachments/assets/1cb43548-5d09-48f6-a8a8-288857f23dbf)




