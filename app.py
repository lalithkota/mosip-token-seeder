import os

import mosip_token_seeder

from mosip_token_seeder import authenticator, authtokenapi, tokenseeder

config = mosip_token_seeder.init_config()
#app = mosip_token_seeder.init_app(config)
logger = mosip_token_seeder.init_logger(config)
# scheduler = mosip_token_seeder.init_scheduler(app, config, logger)

#if config.db.print_password_on_startup:
#    logger.info('DB Password: %s' % config.db.password)
mosip_authenticator = authenticator.initialize(config, logger)
#token_seeder = tokenseeder.initialize(config, logger, mosip_authenticator)
#authtokenapi.initialize(app, config, logger, token_seeder.request_id_queue, authenticator=mosip_authenticator)
#if config.cleanup.enabled:
#    mosip_token_seeder.add_cleanup_job(scheduler, config, token_seeder.cleanup_old_entries)
