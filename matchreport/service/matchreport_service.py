from gamedays.models import Gameinfo
from gamedays.service.gameday_service import EMPTY_DATA
from matchreport.service.model_wrapper import MachtreportModelWrapper

class EmptyPasscheckDetailsTable:
    def to_html(self, *args, **kwargs):
        return "Empty Gameday Passcheck Details Table"

    def to_json(self, *args, **kwargs):
        return EMPTY_DATA


class EmptyMatchReportService:
    def get_staff_passcheck_details(self):
        return EmptyPasscheckDetailsTable()


class MatchreportService:
    @classmethod
    def create(cls, gameday_pk):
        try:
            return cls(gameday_pk)
        except Gameinfo.DoesNotExist:
            return EmptyMatchReportService()

    def __init__(self, pk):
        self.mmw = MachtreportModelWrapper(pk)
        self.gameday_pk = pk


    def get_staff_passcheck_details(self):
        return self.mmw.get_staff_passcheck_details(self.gameday_pk)

