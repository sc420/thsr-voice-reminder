# THSR Voice Reminder

A [Taiwan High Speed Rail](https://www.thsrc.com.tw/index_en.html) (THSR) voice reminder.

## Features

* Uses text-to-speech to remind any text before the arrival/departure of a THSR train
* Automatically finds the latest train before the specified time
* Reload the settings every 10 seconds (We can update settings file without restarting the program)
* Detects alert info from THSR

## Requirements

* Python 3.5 or up
* Network connection is OK

## Installation

1. `pip install -e .`

## Examples

* `python thsr_voice_reminder/main.py --settings=settings/example.yml`

## Potential Problems

* Playing speech will block the thread which checks the reminders every 10 seconds. Don't use long text.
* Don't restart the program or call the API too often, MOTC Transport API has [rate limiting](https://ptxmotc.gitbooks.io/ptx-api-documentation/content/hui-yuan-shen-qing/membertype.html)

## References

* [MOTC Transport API V2](https://ptx.transportdata.tw/MOTC)
