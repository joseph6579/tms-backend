from organisations.models import OrganisationConfiguration
from commons.constants import OrderStatusConfiguration


class OrganisationConfigService:
    @staticmethod
    def update_status_config(config: OrganisationConfiguration, config_data: dict) -> OrganisationConfiguration:
        # Validate with Pydantic
        print('Just before here')
        config_model = OrderStatusConfiguration.model_validate(config_data)
        # Save back into Django model
        config_json = config_model.model_dump(by_alias=True)
        config.order_status_configuration = config_json
        config.save(update_fields=["order_status_configuration"])
        return config
