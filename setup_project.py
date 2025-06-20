import os

folders = ["data"]

files = [
    "README.md",
    "requirements.txt",
    ".gitignore",
    "main.py",
    "company_utils.py",
    "youtube_utils.py",
    "podcast_utils.py",
    "summarization.py",
    "cache_utils.py"
]

# Create folders
for folder in folders:
    os.makedirs(folder, exist_ok=True)

# Create empty files (if they don't exist)
for file in files:
    if not os.path.exists(file):
        with open(file, "w") as f:
            pass

print("✅ LeadPrep AI folder and files created.")