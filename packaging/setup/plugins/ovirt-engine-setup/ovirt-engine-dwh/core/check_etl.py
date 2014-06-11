#
# ovirt-engine-setup -- ovirt engine setup
# Copyright (C) 2014 Red Hat, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#


import re
import gettext
_ = lambda m: gettext.dgettext(message=m, domain='ovirt-engine-dwh')


from otopi import util
from otopi import plugin


from ovirt_engine_setup.dwh import constants as odwhcons
from ovirt_engine_setup.engine_common import database
from ovirt_engine_setup.engine_common \
    import constants as oengcommcons


@util.export
class Plugin(plugin.PluginBase):

    _RE_VERSION = re.compile(
        flags=re.VERBOSE,
        pattern=r"""
            ^
            (?P<major>(\d+))
            \.
            (?P<minor>(\d+))
            \.
            (?P<patch_level>(\d+))
            (?P<extra>.*)
            $
        """,
    )

    def _parseVersionString(self, string):
        matcher = self._RE_VERSION.match(string)
        return (
            matcher.group('major'),
            matcher.group('minor'),
            matcher.group('patch_level')
        )

    def __init__(self, context):
        super(Plugin, self).__init__(context=context)

    @plugin.event(
        stage=plugin.Stages.STAGE_VALIDATION,
        condition=lambda self: (
            self.environment[odwhcons.CoreEnv.ENABLE] and
            not self.environment[oengcommcons.EngineDBEnv.NEW_DATABASE]
        ),
    )
    def _validation(self):
        statement = database.Statement(
            dbenvkeys=oengcommcons.Const.ENGINE_DB_ENV_KEYS,
            environment=self.environment,
        )

        # TODO: in the future go for a new API to fetch this value
        result = statement.execute(
            statement="""
                select version, option_value
                from vdc_options
                where option_name = %(name)s
            """,
            args=dict(
                name='MinimalETLVersion',
            ),
            ownConnection=True,
        )
        if not result:
            raise RuntimeError(
                _('Cannot find MinimalETLVersion in vdc_options')
            )
        minimalVersion = result[0]['option_value']

        minMajor, minMinor, minPatchLevel = self._parseVersionString(
            minimalVersion
        )
        if not (
            (int(odwhcons.Const.VERSION_MAJOR) == int(minMajor)) and
            (int(odwhcons.Const.VERSION_MINOR) == int(minMinor)) and
            (int(odwhcons.Const.VERSION_PATCH_LEVEL) >= int(minPatchLevel))
        ):
            raise RuntimeError(
                _(
                    'Minimal supported DWH version on the engine side is '
                    '{minimal}, and is incompatible with installed DWH '
                    'package version {major}.{minor}.{patch_level}. Please '
                    'upgrade or downgrade engine or DWH as applicable.'
                ).format(
                    minimal=minimalVersion,
                    major=odwhcons.Const.VERSION_MAJOR,
                    minor=odwhcons.Const.VERSION_MINOR,
                    patch_level=odwhcons.Const.VERSION_PATCH_LEVEL,
                )
            )


# vim: expandtab tabstop=4 shiftwidth=4