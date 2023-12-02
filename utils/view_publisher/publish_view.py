import argparse
import json
from pprint import pprint

from slack_sdk.web.client import WebClient

parser = argparse.ArgumentParser(description="Easily POST your App Home view to Slack")

parser.add_argument("userid", help="Slack ID of the user to whom the view is published")
parser.add_argument(
    "viewfile",
    help='JSON file that contains the view made with Block Kit Builder. It should contain two keys: "type" and "blocks".',
)

args = parser.parse_args()

with open(args.viewfile) as viewfile:
    viewdict = json.load(viewfile)

bot_token = input("input bot token (xoxb-*): ")
client = WebClient(token=bot_token)
response = client.views_publish(user_id=args.userid, view=viewdict)


res_data = response.data
if res_data["ok"]:
    print("Successfully published the view.")
else:
    print(f"Error occured: {res_data['error']}")
    print("Full response:")
    pprint(res_data)
