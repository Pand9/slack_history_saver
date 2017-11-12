# Slack history saver
Save Slack history as JSON and CSV.

Download the whole history of specific channel to the full JSON file and to minimal, human-readable CSV.

# Usage
To access your Slack channel programatically, you need access token. Go to https://api.slack.com/custom-integrations/legacy-tokens, click "Create token", copy it and save in a file `secret.txt`.

Python 3 and `slackclient` module are also required:
    
    pip3 install slackclient

That's it. Now you can use the script like this:

    main.py --help
    main.py -s <path to secret.txt> --channel <channel name> [--csv output.csv] [--json output.json]

