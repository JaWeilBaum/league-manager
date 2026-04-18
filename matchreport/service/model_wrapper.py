import pandas as pd

from gamedays.models import Gameinfo
from passcheck.models import PasscheckVerification


class MachtreportModelWrapper:

    def __init__(self, pk, additional_columns=[]):
        gameinfo = Gameinfo.objects.filter(gameday_id=pk)
        if not gameinfo.exists():
            raise Gameinfo.DoesNotExist
        self.gameday = gameinfo.first().gameday
        self._gameinfo: pd.DataFrame = pd.DataFrame(gameinfo.values(
            # select the fields which should be in the dataframe
            *(
                    [f.name for f in Gameinfo._meta.local_fields]
                    + ["officials__name"]
                    + additional_columns
            )
        )
        )
        if self._gameinfo.empty:
            raise Gameinfo.DoesNotExist

    def get_staff_passcheck_details(self, gameday_id):
        column_mapping = {
            "created_at": "Zeitpunkt",
            "official_name": "Schiedsrichter",
            "user__username": "Account",
            "team__name": "Team",
            "note": "Notiz",
        }

        passchecks = pd.DataFrame(
            PasscheckVerification.objects.filter(gameday_id=gameday_id).values(
                *column_mapping.keys()
            )
        )

        if passchecks.empty:
            return pd.DataFrame([], columns=column_mapping.values())

        passchecks["created_at"] = passchecks.created_at.dt.strftime(
            "%Y-%m-%d %H:%M:%S"
        )
        passchecks["note"] = passchecks.note.apply(lambda x: x.replace("\n", "</br>"))

        return passchecks.rename(columns=column_mapping)