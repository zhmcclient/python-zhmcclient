# Support for multiple sessions in zhmcclient mock support

Issue https://github.com/zhmcclient/python-zhmcclient/issues/1437 asks for
adding support for unique session IDs in the zhmcclient mock support.

There are two aspects to this:
1. Generating a unique session ID
2. Supporting multiple FakedSession objects for the same FakedHmc object

The first aspect can easily be implemented with the current design.

The difficulty for the second aspect is that the current design makes the
FakedHmc object a data item within the FakedSession object that is automatically
generated, whereas a proper session support would work such that the FakedHmc
object exists independent of the FakedSession object, and multiple FakedSession
objects could be created against the same FakedHmc object.

This document describes the relevant parts of the current design, to have a
basis for a future support for multiple FakedSession objects for the same
FakedHmc object.

## Current design

class FakedHmc(FakedBaseResource):

    init parms:
        session, hmc_name, hmc_version, api_version
    attributes:
        super(FakedHmc, self).__init__(
            manager=None, properties=None)
        self._session = session     # FakedSession object
        self.hmc_name = hmc_name
        self.hmc_version = hmc_version
        self.api_version = api_version

        self.cpcs = FakedCpcManager(...)
        self.metrics_contexts = FakedMetricsContextManager(...)
        self.consoles = FakedConsoleManager(...)

        self._metric_groups
        self._metric_values

        self.all_resources
        self._enabled

class FakedSession(zhmcclient.Session):

    init parms:
        host, hmc_name, hmc_version, api_version, userid=None, password=None
    attributes:
        super(FakedSession, self).__init__(
            host, userid=userid, password=password)
        self._hmc = FakedHmc(self, hmc_name, hmc_version, api_version)
        self._urihandler = UriHandler(URIS)
        self._object_topic = 'faked-notification-topic'
        self._job_topic = 'faked-job-notification-topic'

Handler for "Logon" (POST /api/sessions):

    def post(method, hmc, uri, uri_parms, body, logon_required,
             wait_for_completion):
        assert wait_for_completion is True  # synchronous operation
        check_required_fields(method, uri, body, ['userid', 'password'])
        result = {
            'api-session': 'fake-session-id',
            'notification-topic': 'fake-topic-1',
            'job-notification-topic': 'fake-topic-2',
            'api-major-version': 4,
            'api-minor-version': 40,
            'password-expires': -1,
            # 'shared-secret-key' not included
            'session-credential': uuid.uuid4().hex,
        }
        return result

Handler for "Logoff" (DELETE /api/sessions/this-session):

    def delete(method, hmc, uri, uri_parms, logon_required):
        pass

Typical use:

      session = FakedSession('fake-host', 'fake-hmc', '2.13.1', '1.8')
      session.hmc.consoles.add({
          'object-id': None,
          # object-uri will be automatically set
          'parent': None,
          'class': 'console',
          'name': 'fake-console1',
          'description': 'Console #1',
      })

      # From here on, normal zhmcclient classes/methods are used:
      client = Client(session)
      console = client.consoles.find(name=...)
