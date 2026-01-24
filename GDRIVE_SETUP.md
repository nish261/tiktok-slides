# Google Drive Auto-Upload Setup

## One-Time Setup (Do this first!)

### Step 1: Configure rclone with Google Drive

Run this command and follow the prompts:

```bash
rclone config
```

When prompted:
1. Choose `n` for "New remote"
2. Name it: `gdrive`
3. Choose `drive` (Google Drive) from the list
4. Leave client_id and client_secret blank (press Enter)
5. Choose scope `1` (Full access)
6. Leave root_folder_id blank (press Enter)
7. Leave service_account_file blank (press Enter)
8. Choose `n` for advanced config
9. Choose `y` to auto config (it will open a browser)
10. **Sign in to your Google account** in the browser
11. Choose `y` to confirm
12. Choose `q` to quit config

### Step 2: Test the connection

```bash
rclone lsd gdrive:
```

This should list your Google Drive folders. If it works, you're all set!

---

## How to Use

### Manual Upload (after generating slides):

```bash
# Upload a specific variation folder
python3 upload_to_gdrive.py sample_content/output/variation1

# Or upload all output
python3 upload_to_gdrive.py sample_content/output

# Upload to a specific Google Drive folder
python3 upload_to_gdrive.py sample_content/output "My Slides Folder"
```

### Auto-Upload After Generation:

The slides will automatically upload to Google Drive when you generate them through the app!

---

## Troubleshooting

**Error: "Remote 'gdrive' not found"**
- Run `rclone config` again and make sure you named it exactly `gdrive`

**Error: "Authentication failed"**
- Run `rclone config reconnect gdrive:` to refresh your Google account connection

**Uploads are slow**
- This is normal for large batches. You can monitor progress in the terminal.

---

## Where Your Files Go

By default, uploads go to: `Google Drive/TikTok Slides/`

You can change this by editing the `gdrive_folder` parameter in the script.
