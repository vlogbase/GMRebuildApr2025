{
  "files": [
    ".replit",
    "replit.nix",
    ".config/nix/replit.toml"
  ],
  "language": "python3",
  "run": "PORT=3000 python3 app_workflow.py",
  "configure": {
    "interpreter": {
      "id": "python-3.11"
    },
    "packager": {
      "manager": "pip",
      "installations": [
        {
          "source": "requirements.txt"
        }
      ]
    }
  }
}