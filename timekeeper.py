import time
from datetime import datetime
import re
from slackclient import SlackClient
import schedule


slack_client = SlackClient('')

timekeeper_id = None

# constants
RTM_READ_DELAY = 1
EXAMPLE_COMMAND = "do"
MENTION_REGEX = "^<@(|[WU].+)>(.*)"

times_to_keep = []

ch = ""

# Following 3 methods taken from tutorial at https://www.fullstackpython.com/blog/build-first-slack-bot-python.html

def parse_bot_commands(slack_events):
    """
        Parses a list of events coming from the Slack RTM API to find bot commands.
        If a bot command is found, this function returns a tuple of command and channel.
        If its not found, then this function returns None, None.
    """
    for event in slack_events:
        if event["type"] == "message" and not "subtype" in event:
            user_id, message = parse_direct_mention(event["text"])
            if user_id == starterbot_id:
                return message, event["channel"]
    return None, None

def parse_direct_mention(message_text):
    """
        Finds a direct mention (a mention that is at the beginning) in message text
        and returns the user ID which was mentioned. If there is no direct mention, returns
None
    """
    matches = re.search(MENTION_REGEX, message_text)
    # the first group contains the username, the second group contains the remaining message
    return (matches.group(1), matches.group(2).strip()) if matches else (None, None)

def handle_command(command, channel):
    """
        Executes bot command if the command is known
    """
    # Default response is help text for the user
    default_response = "Not sure what you mean. Try *{}*.".format(EXAMPLE_COMMAND)

    # Finds and executes the given command, filling in response
    response = None

    if command.startswith("add_date") or command.startswith("add_event") or command.startswith("add_time"):
        words = command.split(" ")
        if(len(words) is not 3):
            response = "Not sure what to do here. Try again with this format: 'add_date [event_name] [MM/DD/YYYY]' or 'add_date [MM/DD/YYY] [event_name]"
        else:
            name = None
            time_obj = None

            try:
                time_obj = datetime.strptime(words[1], '%m/%d/%Y')
                name = words[2]
            except:
                try:
                    time_obj = datetime.strptime(words[2], '%m/%d/%Y')
                    name = words[1]
                except:
                    response = "Please enter a valid date...I can't read that!"

        if name and time_obj:
            if([name, time_obj] in times_to_keep):
                response = "I've already got that in my records!"
            elif(time_obj is not None):
                times_to_keep.append([name, time_obj])
                response = "Thanks! I'll make sure to keep track of " + name
    elif command.startswith("del_date"):
        words = command.split(" ")
        name = words[1]
        if len(words) is not 2:
            response = "Not a valid input. Try 'del_date [name]'"
        else:
            for sublist in times_to_keep:
                if sublist[0] == name:
                    del sublist
                    response = name + "deleted."
                    break
    elif command.startswith("print_dates"):
        words = command.split(" ")
        if len(words) is not 1:
            response = "That's too many arguments! Try '@timekeeper print_dates"
        else:
            response = "Here's what I've got: \n"
            for sublist in times_to_keep:
                response += (sublist[0] + "\t" + str(sublist[1].date().strftime('%b %d, %Y')) + "\n")
    else:
        response = "That's not valid!"

    ch = channel

    # Sends the response back to the channel
    slack_client.api_call(
        "chat.postMessage",
        channel=channel,
        text=response or default_response
    )


def send_reminders():

    message = "Here's today's reminders: \n"

    for sublist in times_to_keep:
        difference = (datetime.now() - sublist[1])
        days = difference.days

        message += sublist[0] + " is " + str(days) + " days away. \n"

    slack_client.api_call(
        "chat.postMessage",
        channel=ch,
        text=message
    )


schedule.every().day.at("19:00").do(send_reminders)


if __name__ == "__main__":
        if slack_client.rtm_connect(with_team_state=False):
                print("Starter Bot connected and running!")

                starterbot_id = slack_client.api_call("auth.test")["user_id"]
                while True:
                        command, channel = parse_bot_commands(slack_client.rtm_read())
                        if command:
                                handle_command(command, channel)
                        time.sleep(RTM_READ_DELAY)
                        schedule.run_pending()

        else:
                print("Connection failed. Exception traceback printed above")
