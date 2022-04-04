"""Generate graph showing mileage over time within a given year."""
import csv
from datetime import datetime, timedelta

import click
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np


def filter_activities(year, file, filter_activity_type):
    """Filter strava activities csv to relevant activities.

    Args:
        year: Year to filter on.
        file: Path to strava activities.csv file.
        filter_activity_type: Run, Walk, Ride, Rowing, Kayaking, etc.

    Returns:
        Array of activities; activity is a dict with `date` and `mileage` keys.
    """
    activities = []
    with open(file, "r") as f:
        reader = csv.reader(f, delimiter=",")
        next(reader, None)  # skip headers
        for row in reader:

            date_str = row[1]
            activity_type = row[3]

            if activity_type != filter_activity_type:
                continue

            # date ex (in utc): Aug 7, 2021, 12:44:45 AM
            date = datetime.strptime(date_str, "%b %d, %Y, %I:%M:%S %p")

            if date.year != year:
                continue

            kilometers = row[6]
            mileage = float(kilometers) * 0.621371
            activities.append({"date": date, "mileage": mileage})
    return activities


def enrich_activities(activities, year):
    """Prepare activities for graphing.

    Returns:
        Array of activities.
    """
    # zero pad days
    days = gen_days(year)
    activities = sorted(activities, key=lambda d: d["date"])
    enriched = []
    for day in days:

        matches = find_matching_activities(day, activities)
        # if no activity on day, add 0 mileage for day
        if not matches:
            enriched.append({"date": day, "mileage": 0})
        else:
            # combine mileage for a single day
            daily_mileage = 0
            for match in matches:
                daily_mileage += match["mileage"]
            enriched.append({"date": matches[0]["date"], "mileage": daily_mileage})
    return enriched


def create_graph(enriched, graph_name: str):
    """Create python graph from activities data."""
    x_vals, y_vals_init = zip(*[(i["date"], np.cumsum(i["mileage"])) for i in enriched])
    y_vals = np.cumsum(y_vals_init)
    y_vals = [round(val, 2) for val in y_vals]
    plt.figure(figsize=(20,10))
    plt.plot(x_vals, y_vals)
    plt.title(graph_name)

    plt.grid()
    ax = plt.gca()

    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=1))
    count = 0
    last_a = 0
    last_b = 0
    for a,b in zip(x_vals, y_vals):
        count += 1
        if count % 30 == 0:
            plt.annotate(xy=(a, b-25), text=str(b))
        last_a = a
        last_b = b

    plt.annotate(xy=(last_a, last_b+20), text=str(last_b))
    plt.savefig(f'{graph_name}.png', bbox_inches='tight')


def find_matching_activities(day, activities):
    """Return activities on given day."""
    matches = []
    for activity in activities:
        activity_date = activity["date"]
        if (
            activity_date.month == day.month
            and activity_date.day == day.day
            and activity_date.year == day.year
        ):
            matches.append(activity)
    return matches


def gen_days(year):
    """Util method to generate days in a year."""
    start_date = datetime(year, 1, 1)
    end_date = datetime(year, 12, 31)
    d = start_date
    dates = [start_date]
    while d < end_date:
        d += timedelta(days=1)
        dates.append(d)
    return dates


@click.command()
@click.option('--year', default=2021, help='Year to generate graph on')
@click.option(
    '--file', default='activities.csv', help='Path to strava activities csv file'
)
@click.option('--activity_type', default='Run', help='Activity Type to filter on')
@click.option('--graph_name', default='2021 Running Mileage', help='Graph title and save file name')
def main(year, file, activity_type, graph_name):
    """Generate graph of mileage accumulation from your strava data archive."""
    activities = filter_activities(year, file, activity_type)
    print(f"Number of {activity_type} activities in year: {len(activities)}")

    enriched = enrich_activities(activities, year)

    create_graph(enriched, graph_name)


if __name__ == "__main__":
    main()
