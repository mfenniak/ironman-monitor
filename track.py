import requests
import time
import random
from bs4 import BeautifulSoup
from twilio.rest import TwilioRestClient
import config

twilio_client = TwilioRestClient(config.twilio_sid, config.twilio_auth)

def main():
    #print repr(fetch_current_state())
    #import sys; sys.exit(0)

    state = None
    while state == None:
        try:
            state = fetch_current_state()
            if state == None:
                print "Error retrieving initial state; sleeping 10s"
                time.sleep(10)
        except KeyboardInterrupt:
            raise
        except:
            print "Error retrieving initial state; sleeping 10s"
            time.sleep(10)

    while True:
        try:
            print "Sleeping 60 seconds..."
            time.sleep(60)
            new_state = fetch_current_state()

            notifications = []
            for (key, new_value) in new_state.iteritems():
                orig_value = state.get(key)
                if orig_value != new_value:
                    notifications.append({"key": key, "new_value": new_value})

            if notifications:
                send_notifications(new_state.get("Athlete"), notifications)

            state = new_state
        except KeyboardInterrupt:
            raise
        except:
            print "Error on updated check state; sleeping 60s"
            time.sleep(60)


def send_notifications(athlete, notifications):
    text = "%s -- " % (athlete)
    for n in notifications:
        text += "%s: %s; " % (n["key"], n["new_value"])
    text = text[:-2]
    print "send_notification", repr(text)
    for target in config.target_numbers:
        message = twilio_client.messages.create(body=text, to=target, from_=config.source_number)


def fetch_current_state():
    r = requests.get(config.url)
    if r.status_code != 200:
        print "status_code %s was not expected" % r.status_code
        return None

    state = {}
    soup = BeautifulSoup(r.text)

    state["Athlete"] = soup.find("h2").text

    state["Transition: Swim-to-Bike"] = soup.find("td", text="T1:  SWIM-TO-BIKE").find_next_sibling("td").text
    state["Transition: Bike-to-Run"] = soup.find("td", text="T2:  BIKE-TO-RUN").find_next_sibling("td").text

    run_splits = soup.find("strong", text="Run Details").parent.parent.find("tbody")
    last_split_key = None
    for run_split in run_splits.find_all("tr"):
        split_name, distance, split_time, race_time, pace, div_rank, overall_rank, gender_rank = [x.text for x in run_split.find_all("td")]
        key = "Run Split @ %s" % split_name
        state[key + " Time"] = split_time
        state[key + " Pace"] = pace
        last_split_key = key
    del state[last_split_key + " Time"]
    del state[last_split_key + " Pace"]

    run_total = soup.find("strong", text="Run Details").parent.parent.find("tfoot").find("tr")
    split_name, distance, split_time, race_time, pace, div_rank, overall_rank, gender_rank = [x.text for x in run_total.find_all("td")]
    state["Run Total Time"] = split_time
    state["Run Total Pace"] = pace

    bike_splits = soup.find("strong", text="Bike Details").parent.parent.find("tbody")
    for bike_split in bike_splits.find_all("tr"):
        split_name, distance, split_time, race_time, pace, div_rank, overall_rank, gender_rank = [x.text for x in bike_split.find_all("td")]
        key = "Bike Split @ %s" % split_name
        state[key + " Time"] = split_time
        state[key + " Pace"] = pace
        last_split_key = key
    del state[last_split_key + " Time"]
    del state[last_split_key + " Pace"]

    bike_total = soup.find("strong", text="Bike Details").parent.parent.find("tfoot").find("tr")
    split_name, distance, split_time, race_time, pace, div_rank, overall_rank, gender_rank = [x.text for x in bike_total.find_all("td")]
    state["Bike Total Time"] = split_time
    state["Bike Total Pace"] = pace

    #state["Random"] = random.random()

    return state


if __name__ == "__main__":
    main()


