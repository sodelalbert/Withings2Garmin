
import os
from prefect import Flow
from prefect.schedules import clocks, Schedule, filters
from prefect.run_configs import LocalRun
import pendulum
from datetime import timedelta
from sync import main

with Flow('Withings2Garmin') as flow:
    main()

flow.run_config = LocalRun(working_dir=os.getcwd())

flow.schedule = Schedule(
    # fire every hour
    clocks=[clocks.IntervalClock(timedelta(hours=1))],
    # but only on weekdays
    filters=[filters.is_weekday],
    # and only at 10am (offset is 5h to EST)
    or_filters=[
        filters.between_times(pendulum.time(16), pendulum.time(16)),
    ]    
)

flow.register(project_name='garmin')
flow = None
