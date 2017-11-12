#!/usr/bin/python3
import argparse
import logging

import slackclient
import json
import datetime


class UserMap:
    def __init__(self, user_id_to_name):
        self._user_id_to_name = user_id_to_name

    def get_username(self, message):
        if message.get("user"):
            return self._user_id_to_name[message["user"]]
        if message.get("bot_id"):
            return message["bot_id"]
        raise Exception("unknown username: %s" % message)

class APIWrapper:
    def __init__(self, token):
        self._slackclient = slackclient.SlackClient(token)

    def get_messages(self, channel_name):
        """ get all messages from channel """
        channel_id = self._channel_name_to_channel_id(channel_name)
        msgs = []
        while True:
            args = dict(count=1000, channel=channel_id)
            if msgs:
                args["latest"] = msgs[-1]["ts"]
            resp = self._api_call("channels.history", **args)
            msgs += resp["messages"]
            if resp["is_limited"] or not resp["has_more"]:
                break
        return msgs

    def get_user_map(self):
        users = self._api_call("users.list")
        user_map_data = {u["id"]: u["name"] for u in users["members"]}
        return UserMap(user_map_data)

    def _channel_name_to_channel_id(self, channel_name):
        channels = self._api_call("channels.list")
        for c in channels["channels"]:
            if c.get("name") == channel_name:
                return c.get("id")
        raise KeyError("Channel %s not found in %s" % (channel_name, channels))

    def _api_call(self, *a, **kw):
        resp = self._slackclient.api_call(*a, **kw)
        if not resp["ok"]:
            raise Exception("not ok")
        return resp

def nice_ts(tsarg):
    """ prettify timestamp string with microseconds precision
        NOTE: timezones may not always work correctly
    """
    ts, msec = map(int, tsarg.split("."))
    d = datetime.datetime.fromtimestamp(ts)
    d = d.replace(microsecond=msec)
    return d.strftime("%Y-%m-%d %H:%M:%S.%f")

def prettify_text_for_csv(text):
    if "\n" in text:
        text = "\n" + text
    # standard CSV escape character is "
    text = text.replace("\"", "\"\"")
    text = text.replace("\t", "\"\t")
    return text

def make_csv_line(msg):
    """ prefix multiline message with \n, for better reading comfort
        and escape characters, so that CSV can be parsed again
    """
    text = prettify_text_for_csv(msg.get("text", ""))
    return "\t".join([msg["datetime"], msg["username"], text])

def get_pretty_messages(client, channel):
    msgs = client.get_messages(channel)
    user_map = client.get_user_map()

    for m in msgs:
        try:
            m["datetime"] = nice_ts(m["ts"])
            m["username"] = user_map.get_username(m)
            m["csv_line"] = make_csv_line(m)
        except Exception:
            logging.exception("Error with message %s" % m)
    return msgs

def run():
    p = argparse.ArgumentParser(description="Dump slack channel archive in full JSON and human-readable CSV")
    p.add_argument("--channel", default="konfa")
    p.add_argument("-s", "--secret-file", default="secret.txt",
                   help="Get it from https://api.slack.com/custom-integrations/legacy-tokens")
    p.add_argument("--csv", default="output.csv", help="Output csv path")
    p.add_argument("--json", default="output.json", help="Output json path")
    args = p.parse_args()

    client = APIWrapper(open(args.secret_file, "r").read().strip())
    msgs = get_pretty_messages(client, args.channel)
    with open(args.json, "w") as jsonfile:
        json.dump(msgs, jsonfile, indent=4)
    with open(args.csv, "w") as csvfile:
        for l in msgs:
            # noinspection PyTypeChecker
            print(l["csv_line"], file=csvfile)

if __name__ == "__main__":
    run()