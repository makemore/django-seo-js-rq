import re
from django_seo_js import settings
from django_seo_js.backends import SelectedBackend
from django_seo_js.helpers import request_should_be_ignored
from django.http import HttpResponse

# ,# HttpResponseNotFound, Http404, HttpResponseRedirect, HttpResponsePermanentRedirect

import logging

logger = logging.getLogger(__name__)
import django_rq


def process_url(url):
    uam = UserAgentMiddleware()
    uam.backend.get_response_for_url_return_nothing(url)


class UserAgentMiddleware(SelectedBackend):
    def __init__(self, *args, **kwargs):
        super(UserAgentMiddleware, self).__init__(*args, **kwargs)
        regex_str = "|".join(settings.USER_AGENTS)
        regex_str = ".*?(%s)" % regex_str
        self.USER_AGENT_REGEX = re.compile(regex_str, re.IGNORECASE)

    def process_request(self, request):
        background = request.GET.get("background", None)

        if not settings.ENABLED:
            return

        if request_should_be_ignored(request):
            return

        if "HTTP_USER_AGENT" not in request.META:
            return

        if not self.USER_AGENT_REGEX.match(request.META["HTTP_USER_AGENT"]):
            return

        url = self.backend.build_absolute_uri(request)

        if background == "true":
            url = url.replace("?background=true", "")
            queue = django_rq.get_queue('low')
            queue.enqueue(process_url, url, job_timeout=3600)
            return
        try:
            return self.backend.get_response_for_url(url, request)
        except Exception as e:
            logger.exception(e)
