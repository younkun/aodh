#!/usr/bin/env python
#
# Copyright 2013 Red Hat, Inc
# Copyright 2012-2015 eNovance <licensing@enovance.com>
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.
import os
import socket

from keystonemiddleware import opts as ks_opts
from oslo_config import cfg
from oslo_db import options as db_options
import oslo_i18n
from oslo_log import log
from oslo_messaging import opts as msg_opts
from oslo_policy import opts as policy_opts

from aodh import messaging


OPTS = [
    cfg.StrOpt('host',
               default=socket.gethostname(),
               help='Name of this node, which must be valid in an AMQP '
               'key. Can be an opaque identifier. For ZeroMQ only, must '
               'be a valid host name, FQDN, or IP address.'),
    cfg.IntOpt('notification_workers',
               default=1,
               help='Number of workers for notification service. A single '
               'notification agent is enabled by default.'),
    cfg.IntOpt('http_timeout',
               default=600,
               help='Timeout seconds for HTTP requests. Set it to None to '
                    'disable timeout.'),
    cfg.IntOpt('evaluation_interval',
               default=60,
               help='Period of evaluation cycle, should'
               ' be >= than configured pipeline interval for'
               ' collection of underlying meters.',
               deprecated_group='alarm',
               deprecated_opts=[cfg.DeprecatedOpt(
                   'threshold_evaluation_interval', group='alarm')]),
]


CLI_OPTS = [
    cfg.StrOpt('os-username',
               default=os.environ.get('OS_USERNAME', 'aodh'),
               help='User name to use for OpenStack service access.'),
    cfg.StrOpt('os-password',
               secret=True,
               default=os.environ.get('OS_PASSWORD', 'admin'),
               help='Password to use for OpenStack service access.'),
    cfg.StrOpt('os-tenant-id',
               default=os.environ.get('OS_TENANT_ID', ''),
               help='Tenant ID to use for OpenStack service access.'),
    cfg.StrOpt('os-tenant-name',
               default=os.environ.get('OS_TENANT_NAME', 'admin'),
               help='Tenant name to use for OpenStack service access.'),
    cfg.StrOpt('os-cacert',
               default=os.environ.get('OS_CACERT'),
               help='Certificate chain for SSL validation.'),
    cfg.StrOpt('os-auth-url',
               default=os.environ.get('OS_AUTH_URL',
                                      'http://localhost:5000/v2.0'),
               help='Auth URL to use for OpenStack service access.'),
    cfg.StrOpt('os-region-name',
               default=os.environ.get('OS_REGION_NAME'),
               help='Region name to use for OpenStack service endpoints.'),
    cfg.StrOpt('os-endpoint-type',
               default=os.environ.get('OS_ENDPOINT_TYPE', 'publicURL'),
               help='Type of endpoint in Identity service catalog to use for '
                    'communication with OpenStack services.'),
    cfg.BoolOpt('insecure',
                default=False,
                help='Disables X.509 certificate validation when an '
                     'SSL connection to Identity Service is established.'),
    cfg.StrOpt('os-user-domain-id',
               default=os.environ.get('OS_USER_DOMAIN_ID', 'default'),
               help='The domain id of the user'),
    cfg.StrOpt('os-project-domain-id',
               default=os.environ.get('OS_PROJECT_DOMAIN_ID', 'default'),
               help='The domain id of the user project'),
    cfg.StrOpt('os-project-name',
               default=os.environ.get('OS_PROJECT_NAME', 'admin'),
               help='The user project name'),
]


def prepare_service(argv=None):
    conf = cfg.ConfigOpts()
    oslo_i18n.enable_lazy()
    log.register_options(conf)
    log_levels = (conf.default_log_levels +
                  ['stevedore=INFO', 'keystoneclient=INFO'])
    log.set_defaults(default_log_levels=log_levels)
    db_options.set_defaults(conf)
    policy_opts.set_defaults(conf)
    for group, options in ks_opts.list_auth_token_opts():
        conf.register_opts(list(options), group=group)
    # FIXME(jd) We can use that with oslo.messaging>2.0.0:
    # msg_opts.set_defaults(conf)
    for group, options in msg_opts.list_opts():
        conf.register_opts(list(options),
                           group=None if group == "DEFAULT" else group)

    from aodh import opts
    # Register our own Aodh options
    for group, options in opts.list_opts():
        conf.register_opts(list(options),
                           group=None if group == "DEFAULT" else group)

    conf(argv, project='aodh', validate_default_values=True)
    log.setup(conf, 'aodh')
    messaging.setup()
    return conf
