# Copyright 2016 IBM Corp. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import click
import zhmcclient
from _cmd_helper import *

def cmd_session_create(cmd_ctx):
    session = cmd_ctx.session
    try:
        session.logon()
        click.echo("export ZHMC_HOST=%s" % (session.host))
        click.echo("export ZHMC_USERID=%s" % (session.userid))
        click.echo("export ZHMC_SESSION_ID=%s" % (session.session_id))
    except zhmcclient.AuthError as exc:
        click.echo("Logon failed.")
        click.echo("%s: %s" % (exc.__class__.__name__, exc))
    except zhmcclient.Error as exc:
        click.echo("%s: %s" % (exc.__class__.__name__, exc))


def cmd_session_delete(cmd_ctx):
    """Deletes the current session."""
    if not cmd_ctx.is_active_session:
        click.echo('Session is not available.')
        return
    session = cmd_ctx.session
    try:
        session.logoff()
    except zhmcclient.AuthError as exc:
        click.echo("Logoff failed.")
        click.echo("%s: %s" % (exc.__class__.__name__, exc))
    except zhmcclient.Error as exc:
        click.echo("%s: %s" % (exc.__class__.__name__, exc))
    finally:
        click.echo("unset ZHMC_SESSION_ID")
