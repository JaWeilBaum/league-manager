from datetime import datetime

import pandas as pd
from django.apps import apps
from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Max
from django.db.models.functions import ExtractYear
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.utils.functional import cached_property
from django.views import View
from django.views.generic import (
    DetailView,
    UpdateView,
    CreateView,
    FormView,
    DeleteView,
    TemplateView,
)
from formtools.wizard.views import SessionWizardView

from gamedays.service.gameday_service import GamedayService
from league_manager.utils.url_service import UrlService
from league_table.constants import LEAGUE_TABLE_OVERALL_TABLE_BY_SLUG_AND_LEAGUE
from league_table.models import LeagueSeasonConfig, OverrideOfficialGamedaySetting
from league_table.service.leaguetable_repository import LeagueTableRepository
from liveticker.constants import LIVETICKER_HOME

from .constants import (
    MATCHREPORT_GAMEDAY_LIST_AND_YEAR_AND_LEAGUE,
    MATCHREPORT_GAMEDAY_LIST,
    MATCHREPORT_GAMEDAY_LIST_AND_YEAR
)

from gamedays.models import Gameday, Gameinfo
from .service.matchreport_service import MatchreportService


# Create your views here.
class MatchreportGamedayListView(View):
    template_name = "matchreport/gameday_list.html"

    def get(self, request, **kwargs):
        year = kwargs.get("season", datetime.today().year)
        league = kwargs.get("league")
        gamedays = Gameday.objects.filter(date__year=year).order_by("-date")
        gamedays_filtered_by_league = (
            gamedays.filter(league__name=league) if league else gamedays
        )
        return render(
            request,
            self.template_name,
            {
                "gamedays": gamedays_filtered_by_league,
                "years": Gameday.objects.annotate(year=ExtractYear("date"))
                .values_list("year", flat=True)
                .distinct()
                .order_by("-year"),
                "season": year,
                "leagues": gamedays.values_list("league__name", flat=True)
                .distinct()
                .order_by("-league__name"),
                "current_league": league,
                "season_year_pattern": MATCHREPORT_GAMEDAY_LIST_AND_YEAR,
                "season_year_league_pattern": MATCHREPORT_GAMEDAY_LIST_AND_YEAR_AND_LEAGUE,
            },
        )

class MatchreportGamedayDetailView(DetailView):
    template_name = "matchreport/gameday_detail.html"
    model = Gameday

    def get_context_data(self, **kwargs):
        context = super(MatchreportGamedayDetailView, self).get_context_data()
        gameday = context["gameday"]
        ms = MatchreportService.create(gameday.pk)
        render_configs = {
            "index": False,
            "classes": [
                "table",
                "table-hover",
                "table-condensed",
                "table-responsive",
                "text-center",
            ],
            "border": 0,
            "justify": "left",
            "escape": False,
            "table_id": "schedule",
        }
        if "officials" in settings.INSTALLED_APPS:
            show_official_names = False
            if self.request.user.is_staff:
                show_official_names = True
            from officials.service.signup_service import OfficialSignupService

            officials = OfficialSignupService.get_signed_up_officials(
                gameday.pk, show_official_names
            )
        else:
            officials = []


        passcheck_info_table = ""

        if self.request.user.is_staff:
            passcheck_info_table = ms.get_staff_passcheck_details().to_html(
                **render_configs
            )

        context["info"] = {
            "officials": officials,
            "passcheck_info_table": passcheck_info_table,
            "url_pattern_liveticker": f"{UrlService.build_absolute_url(LIVETICKER_HOME)}?league={gameday.league.name}&gameday={gameday.pk}",
        }

        return context