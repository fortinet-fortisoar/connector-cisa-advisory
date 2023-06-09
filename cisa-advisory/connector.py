from connectors.core.connector import Connector, get_logger, ConnectorError
from .operations import operations

logger = get_logger("cisa-advisory")
class Advisory(Connector):
    def execute(self, config, operation, params, **kwargs):
        try:
            config['connector_info'] = {"connector_name": self._info_json.get('name'),
                "connector_version": self._info_json.get('version')}
            operation = operations.get(operation)
            if not operation:
                logger.error('Unsupported operation: {}'.format(operation))
                raise ConnectorError('Unsupported operation')
            return operation(config, params)
        except Exception as err:
            logger.exception(err)
            raise ConnectorError(err)