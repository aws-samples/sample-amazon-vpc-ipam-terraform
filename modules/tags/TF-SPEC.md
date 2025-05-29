<!-- BEGIN_TF_DOCS -->

## Inputs

| Name                                                                     | Description                                                                                                    | Type          | Default | Required |
| ------------------------------------------------------------------------ | -------------------------------------------------------------------------------------------------------------- | ------------- | ------- | :------: |
| <a name="input_business_unit"></a> [business_unit](#input_business_unit) | Business Unit for the resource being deployed                                                                  | `string`      | n/a     |   yes    |
| <a name="input_environment"></a> [environment](#input_environment)       | Environment for the resource being deployed                                                                    | `string`      | n/a     |   yes    |
| <a name="input_feature_name"></a> [feature_name](#input_feature_name)    | Feature name for the resource being deployed                                                                   | `string`      | n/a     |   yes    |
| <a name="input_product_name"></a> [product_name](#input_product_name)    | Product name for the resource being deployed                                                                   | `string`      | n/a     |   yes    |
| <a name="input_optional_tags"></a> [optional_tags](#input_optional_tags) | Map of any non-required tags to include in the default tags. Will be appended to this module's tag_map output. | `map(string)` | `{}`    |    no    |

## Outputs

| Name                                                     | Description                                           |
| -------------------------------------------------------- | ----------------------------------------------------- |
| <a name="output_tag_map"></a> [tag_map](#output_tag_map) | Return the full map of all required and optional tags |

<!-- END_TF_DOCS -->
